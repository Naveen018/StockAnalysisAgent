import os
from dotenv import load_dotenv
import finnhub
import requests
import json
import logging
import time
from datetime import datetime, timedelta
from ...models import TickerNews, NewsArticle
from ...config import SUPPORTED_TIMEFRAMES, QUARTER_PATTERN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

class TickerNewsFetcher:
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        self.client = finnhub.Client(api_key=self.api_key)
        logger.info("TickerNewsFetcher initialized with Finnhub API key")

    def _get_quarter_dates(self, timeframe: str, current_date: datetime) -> tuple[datetime, datetime]:
        """Determine the start and end dates for the given timeframe or specific quarter."""
        logger.info(f"Calculating date range for timeframe: '{timeframe}'")
        # Normalize and check for specific quarter (e.g., "2023 Q2")
        normalized_timeframe = timeframe.strip()
        quarter_match = QUARTER_PATTERN.match(normalized_timeframe)
        if quarter_match:
            year = int(quarter_match.group(1))
            quarter = int(quarter_match.group(2))
            if quarter == 1:
                start_date = datetime(year, 1, 1)
                end_date = datetime(year, 3, 31)
            elif quarter == 2:
                start_date = datetime(year, 4, 1)
                end_date = datetime(year, 6, 30)
            elif quarter == 3:
                start_date = datetime(year, 7, 1)
                end_date = datetime(year, 9, 30)
            else:  # Q4
                start_date = datetime(year, 10, 1)
                end_date = datetime(year, 12, 31)
            logger.info(f"Determined specific quarter Q{quarter} {year}: {start_date} to {end_date}")
            return start_date, end_date

        # Handle relative timeframes
        to_date = current_date
        timeframe_lower = timeframe.lower().strip()
        if timeframe_lower in ["today", "daily"]:
            from_date = to_date - timedelta(days=1)
        elif timeframe_lower in ["last 2 days", "2 days"]:
            from_date = to_date - timedelta(days=2)
        elif timeframe_lower in ["last 3 days", "3 days"]:
            from_date = to_date - timedelta(days=3)
        elif timeframe_lower in ["last week", "weekly"]:
            from_date = to_date - timedelta(days=7)
        elif timeframe_lower in ["last month", "monthly"]:
            from_date = to_date - timedelta(days=30)
        elif timeframe_lower in ["last quarter", "quarterly"]:
            current_month = current_date.month
            current_year = current_date.year
            if current_month >= 4:  # Q1 (Jan-Mar) complete
                from_date = datetime(current_year, 1, 1)
                to_date = datetime(current_year, 3, 31)
            elif current_month >= 7:  # Q2 (Apr-Jun) complete
                from_date = datetime(current_year, 4, 1)
                to_date = datetime(current_year, 6, 30)
            elif current_month >= 10:  # Q3 (Jul-Sep) complete
                from_date = datetime(current_year, 7, 1)
                to_date = datetime(current_year, 9, 30)
            else:  # Q4 of previous year
                from_date = datetime(current_year - 1, 10, 1)
                to_date = datetime(current_year - 1, 12, 31)
            logger.info(f"Determined last quarter: {from_date} to {to_date}")
        elif timeframe_lower in ["last 6 months", "6 months"]:
            from_date = to_date - timedelta(days=180)
        else:  # last year, annually
            from_date = to_date - timedelta(days=365)
        
        logger.info(f"Determined relative timeframe '{timeframe}': {from_date} to {to_date}")
        return from_date, to_date

    async def fetch_news(self, ticker: str, timeframe: str = "last week") -> TickerNews:
        """Fetch recent news articles for the given ticker and timeframe using Finnhub API."""
        logger.info(f"fetch_news called with ticker: '{ticker}', timeframe: '{timeframe}'")
        
        if not ticker.strip():
            logger.warning("Empty ticker received")
            return TickerNews(
                ticker=ticker,
                news=[],
                timeframe=timeframe,
                error="No ticker provided"
            )

        # Validate timeframe
        normalized_timeframe = timeframe.strip()
        supported_timeframes_lower = [tf.lower() for tf in SUPPORTED_TIMEFRAMES]
        is_supported = normalized_timeframe.lower() in supported_timeframes_lower
        is_quarter = bool(QUARTER_PATTERN.match(normalized_timeframe))
        logger.info(f"Timeframe validation: input='{timeframe}', normalized='{normalized_timeframe}', is_supported={is_supported}, is_quarter={is_quarter}, supported_timeframes={supported_timeframes_lower}, quarter_pattern={QUARTER_PATTERN.pattern}")
        
        if not (is_supported or is_quarter):
            logger.warning(f"Unsupported timeframe: '{timeframe}'")
            return TickerNews(
                ticker=ticker,
                news=[],
                timeframe=timeframe,
                error="Invalid timeframe. Please specify a supported timeframe: 'today', 'last 2 days', 'last 3 days', 'last week', 'last month', 'last quarter', 'last 6 months', 'last year', 'annually', or 'YYYY QN' (e.g., '2023 Q2')"
            )

        # Get date range
        try:
            from_date, to_date = self._get_quarter_dates(normalized_timeframe, datetime.now())
        except Exception as e:
            logger.error(f"Error calculating date range for timeframe '{timeframe}': {str(e)}")
            return TickerNews(
                ticker=ticker,
                news=[],
                timeframe=timeframe,
                error=f"Failed to calculate date range: {str(e)}"
            )
        
        from_date_str = from_date.strftime("%Y-%m-%d")
        to_date_str = to_date.strftime("%Y-%m-%d")
        logger.info(f"Fetching news for {ticker} from {from_date_str} to {to_date_str}")

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching Finnhub news for {ticker} (attempt {attempt})")
                url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date_str}&to={to_date_str}&token={self.api_key}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                news_results = response.json()
                logger.info(f"Finnhub news results: {json.dumps(news_results, indent=2)}")

                if not news_results or len(news_results) == 0:
                    logger.warning(f"No news found for {ticker} on attempt {attempt}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerNews(
                        ticker=ticker,
                        news=[],
                        timeframe=timeframe,
                        error="No news articles found for the given ticker and timeframe"
                    )

                # Process news articles (limit to 10 for analysis)
                articles = []
                for item in news_results[:10]:
                    published_at = datetime.fromtimestamp(item["datetime"]).strftime("%Y-%m-%d")
                    articles.append(NewsArticle(
                        headline=item["headline"],
                        source=item["source"],
                        published_at=published_at,
                        summary=item.get("summary"),
                        url=item.get("url")
                    ))

                result = TickerNews(
                    ticker=ticker,
                    news=articles,
                    timeframe=timeframe,
                    error=None
                )
                logger.info(f"Successfully fetched news: {len(articles)} articles for {ticker}")
                return result
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error in fetch_news on attempt {attempt}: {str(e)}", exc_info=True)
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerNews(
                    ticker=ticker,
                    news=[],
                    timeframe=timeframe,
                    error=f"Failed after {max_retries} attempts: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error in fetch_news on attempt {attempt}: {str(e)}", exc_info=True)
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerNews(
                    ticker=ticker,
                    news=[],
                    timeframe=timeframe,
                    error=f"Failed after {max_retries} attempts: {str(e)}"
                )