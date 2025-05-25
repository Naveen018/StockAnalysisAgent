import os
from dotenv import load_dotenv
import finnhub
import requests
import json
import logging
import time
from datetime import datetime, timedelta
from ...models import TickerNews, NewsArticle
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# --- Ticker News Logic ---
class TickerNewsFetcher:
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        self.client = finnhub.Client(api_key=self.api_key)
        logger.info("TickerNewsFetcher initialized with Finnhub API key")

    async def fetch_news(self, ticker: str) -> TickerNews:
        """Fetch recent news articles for the given ticker using Finnhub API."""
        logger.info(f"fetch_news called with ticker: {ticker}")
        
        if not ticker.strip():
            logger.warning("Empty ticker received")
            return TickerNews(
                ticker=ticker,
                news=[],
                error="No ticker provided"
            )

        # Set date range: last 7 days
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        logger.info(f"Fetching news for {ticker} from {from_date} to {to_date}")

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching Finnhub news for {ticker} (attempt {attempt})")
                # Use Finnhub's /v1/company-news endpoint
                url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={self.api_key}"
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
                        error="No news articles found for the given ticker"
                    )

                # Process news articles
                articles = []
                for item in news_results[:5]:  # Limit to 5 articles for brevity
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
                    error=f"Failed after {max_retries} attempts: {str(e)}"
                )