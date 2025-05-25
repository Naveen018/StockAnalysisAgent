import logging
import requests
import json
import time
from datetime import datetime, timedelta, UTC
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

from ...config import (
    POLYGON_API_KEY,
    POLYGON_BASE_URL,
    SUPPORTED_TIMEFRAMES,
)
from ...models import PriceChange, TickerPriceChange

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TickerPriceChangeCalculator:
    def __init__(self):
        if not POLYGON_API_KEY:
            raise ValueError("POLYGON_API_KEY not found in environment variables")
        self.api_key = POLYGON_API_KEY
        logger.info("TickerPriceChangeCalculator initialized with Polygon API key")

    async def calculate_price_change(self, ticker: str, timeframe: str = "last week") -> TickerPriceChange:
        """Calculate stock price change for the given ticker and timeframe using Polygon.io API."""
        logger.info(f"calculate_price_change called with ticker: {ticker}, timeframe: {timeframe}")
        
        if not ticker.strip():
            logger.warning("Empty ticker received")
            return TickerPriceChange(
                ticker=ticker,
                error="No ticker provided"
            )

        if timeframe.lower() not in SUPPORTED_TIMEFRAMES:
            logger.warning(f"Unsupported timeframe: {timeframe}")
            return TickerPriceChange(
                ticker=ticker,
                error="Unsupported timeframe; use 'today' or 'last week'"
            )

        # Determine timeframe and set date range (UTC)
        now = datetime.now(UTC)
        if timeframe.lower() in ["today", "daily"]:
            resolution = "day"
            start_date = now - timedelta(days=1)
            end_date = now
        else:  # last week
            resolution = "day"
            start_date = now - timedelta(days=7)
            end_date = now

        # Format dates for Polygon API (YYYY-MM-DD)
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        start_date_str = from_date
        end_date_str = to_date
        logger.info(f"Fetching price data for {ticker} from {start_date_str} to {end_date_str}")

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching Polygon candles for {ticker} (attempt {attempt})")
                url = f"{POLYGON_BASE_URL}/aggs/ticker/{ticker}/range/1/{resolution}/{from_date}/{to_date}?apiKey={self.api_key}"
                logger.info(f"Request URL (without token): {POLYGON_BASE_URL}/aggs/ticker/{ticker}/range/1/{resolution}/{from_date}/{to_date}")
                response = requests.get(url, timeout=5)
                logger.info(f"Response status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")

                # Check for non-JSON content type
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type.lower():
                    error_msg = "Non-JSON response received"
                    if 'text/html' in content_type.lower() and ('401' in response.text or 'Unauthorized' in response.text):
                        error_msg = "Invalid Polygon API key detected"
                    logger.error(f"{error_msg} for {ticker} on attempt {attempt}: {response.text[:200]}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerPriceChange(
                        ticker=ticker,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        error=f"{error_msg}: {response.text[:100]}; verify POLYGON_API_KEY in .env"
                    )

                # Check for empty response
                if not response.text.strip():
                    logger.warning(f"Empty response for {ticker} on attempt {attempt}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerPriceChange(
                        ticker=ticker,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        error="Empty response from Polygon; check API key or server status"
                    )

                # Parse JSON
                try:
                    data = response.json()
                except RequestsJSONDecodeError as e:
                    logger.error(f"Invalid JSON response for {ticker} on attempt {attempt}: {response.text[:200]}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerPriceChange(
                        ticker=ticker,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        error=f"Invalid API response: {response.text[:100]}; verify POLYGON_API_KEY in .env"
                    )

                logger.info(f"Polygon results: {json.dumps(data, indent=2)}")

                # Check for valid data
                if data.get("status") not in ["OK", "DELAYED"] or not data.get("results"):
                    logger.warning(f"No valid price data for {ticker} on attempt {attempt}: {data.get('error', 'No error message')}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerPriceChange(
                        ticker=ticker,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        error=f"No valid price data: {data.get('error', 'Unknown error')}"
                    )

                # Extract price data
                results = data["results"]
                if len(results) < 2 and timeframe.lower() != "today":
                    logger.warning(f"Insufficient data points for {ticker} on attempt {attempt}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerPriceChange(
                        ticker=ticker,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        error="Insufficient price data for the given timeframe"
                    )

                if timeframe.lower() == "today":
                    # Use open and close of the latest day
                    open_price = results[-1]["o"] if results[-1].get("o") else 0
                    close_price = results[-1]["c"] if results[-1].get("c") else 0
                else:
                    # Use first and last close prices
                    open_price = results[0]["c"] if results[0].get("c") else 0
                    close_price = results[-1]["c"] if results[-1].get("c") else 0

                if open_price == 0:
                    logger.error(f"Invalid start price for {ticker}")
                    return TickerPriceChange(
                        ticker=ticker,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        error="Invalid start price data"
                    )

                # Calculate changes
                absolute_change = close_price - open_price
                percentage_change = (absolute_change / open_price) * 100 if open_price != 0 else 0

                price_change = PriceChange(
                    absolute_change=round(absolute_change, 2),
                    percentage_change=round(percentage_change, 2),
                    start_price=round(open_price, 2),
                    end_price=round(close_price, 2),
                    timeframe=timeframe
                )

                result = TickerPriceChange(
                    ticker=ticker,
                    price_change=price_change,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    error=None
                )
                logger.info(f"Successfully calculated price change for {ticker}: {price_change}")
                return result
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error in calculate_price_change on attempt {attempt}: {str(e)}, Response: {response.text[:200]}")
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerPriceChange(
                    ticker=ticker,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    error=f"Failed after {max_retries} attempts: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error in calculate_price_change on attempt {attempt}: {str(e)}, Response: {response.text[:200] if 'response' in locals() else 'No response'}")
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerPriceChange(
                    ticker=ticker,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    error=f"Failed after {max_retries} attempts: {str(e)}"
                ) 