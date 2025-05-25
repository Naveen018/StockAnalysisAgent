# --- Ticker Price Logic ---
import os
import finnhub
import requests
import json
import logging
import time
from datetime import datetime

from ...models import TickerPrice , PriceData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TickerPriceFetcher:
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        self.client = finnhub.Client(api_key=self.api_key)
        logger.info("TickerPriceFetcher initialized with Finnhub API key")

    async def fetch_price(self, ticker: str) -> TickerPrice:
        """Fetch current stock price for the given ticker using Finnhub API."""
        logger.info(f"fetch_price called with ticker: {ticker}")
        
        if not ticker.strip():
            logger.warning("Empty ticker received")
            return TickerPrice(
                ticker=ticker,
                price=None,
                timestamp=None,
                error="No ticker provided"
            )

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching Finnhub quote for {ticker} (attempt {attempt})")
                # Use Finnhub's /v1/quote endpoint
                url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={self.api_key}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                quote_data = response.json()
                logger.info(f"Finnhub quote results: {json.dumps(quote_data, indent=2)}")

                if not quote_data or quote_data.get("c", 0) == 0:
                    logger.warning(f"No valid price data for {ticker} on attempt {attempt}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerPrice(
                        ticker=ticker,
                        price=None,
                        timestamp=None,
                        error="No valid price data found for the given ticker"
                    )

                # Process price data
                price = PriceData(
                    current=quote_data["c"],
                    open=quote_data["o"],
                    high=quote_data["h"],
                    low=quote_data["l"]
                )
                timestamp = datetime.fromtimestamp(quote_data["t"]).strftime("%Y-%m-%d")

                result = TickerPrice(
                    ticker=ticker,
                    price=price,
                    timestamp=timestamp,
                    error=None
                )
                logger.info(f"Successfully fetched price for {ticker}: {price.current}")
                return result
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error in fetch_price on attempt {attempt}: {str(e)}", exc_info=True)
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerPrice(
                    ticker=ticker,
                    price=None,
                    timestamp=None,
                    error=f"Failed after {max_retries} attempts: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error in fetch_price on attempt {attempt}: {str(e)}", exc_info=True)
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerPrice(
                    ticker=ticker,
                    price=None,
                    timestamp=None,
                    error=f"Failed after {max_retries} attempts: {str(e)}"
                )