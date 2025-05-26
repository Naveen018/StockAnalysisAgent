import os
import requests
import json
import logging
import time
from datetime import datetime
from typing import List
from pydantic import ValidationError
from ...models import TickerAnalysis, SentimentAnalysis, KeyEvent, NewsArticle, TickerPriceChange, TickerPrice, PriceChange
from ...config import FINNHUB_API_KEY, SUPPORTED_TIMEFRAMES, QUARTER_PATTERN

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TickerAnalyzer:
    def __init__(self):
        if not FINNHUB_API_KEY:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        self.api_key = FINNHUB_API_KEY
        logger.info("TickerAnalyzer initialized with Finnhub API key")

    async def analyze_ticker(self, ticker: str, timeframe: str, news: List[NewsArticle], price_change: TickerPriceChange, current_price: TickerPrice) -> TickerAnalysis:
        """Analyze stock price movements using news, price data, and sector trends."""
        try:
            logger.debug(f"Input types - ticker: {type(ticker)}, timeframe: {type(timeframe)}, news: {type(news)}, price_change: {type(price_change)}, current_price: {type(current_price)}")
            logger.debug(f"Raw price_change: {price_change}")
            
            # Coerce news if necessary
            if isinstance(news, list) and news and not all(isinstance(item, NewsArticle) for item in news):
                try:
                    coerced_news = []
                    for item in news:
                        if isinstance(item, dict):
                            if 'published_at' in item and isinstance(item['published_at'], datetime):
                                item['published_at'] = item['published_at'].isoformat()
                            coerced_news.append(NewsArticle(**item))
                        else:
                            logger.warning(f"Skipping invalid news item: {item}")
                            continue
                    news = coerced_news
                    logger.debug("Coerced news to List[NewsArticle]")
                except ValidationError as e:
                    logger.error(f"Failed to coerce news: {str(e)}")
                    return TickerAnalysis(ticker=ticker, timeframe=timeframe, error=f"Invalid news data format: {str(e)}")
            
            # Coerce price_change
            if not isinstance(price_change, TickerPriceChange):
                try:
                    if isinstance(price_change, dict):
                        price_change = TickerPriceChange(**price_change)
                        logger.debug("Coerced price_change to TickerPriceChange")
                    else:
                        logger.error(f"Unexpected price_change type: {type(price_change)}")
                        return TickerAnalysis(ticker=ticker, timeframe=timeframe, error=f"Invalid price_change type: {type(price_change)}")
                except ValidationError as e:
                    logger.error(f"Failed to coerce price_change: {str(e)}")
                    return TickerAnalysis(ticker=ticker, timeframe=timeframe, error=f"Invalid price change data format: {str(e)}")
            
            # Coerce current_price
            if not isinstance(current_price, TickerPrice):
                try:
                    if isinstance(current_price, dict):
                        current_price = TickerPrice(**current_price)
                        logger.debug("Coerced current_price to TickerPrice")
                    else:
                        logger.error(f"Unexpected current_price type: {type(current_price)}")
                        return TickerAnalysis(ticker=ticker, timeframe=timeframe, error=f"Invalid current_price type: {type(current_price)}")
                except ValidationError as e:
                    logger.error(f"Failed to coerce current_price: {str(e)}")
                    return TickerAnalysis(ticker=ticker, timeframe=timeframe, error=f"Invalid current price data format: {str(e)}")

            logger.info(f"analyze_ticker called with ticker: '{ticker}', timeframe: '{timeframe}', news_count: {len(news)}, price_change: {price_change}, current_price: {current_price}")
            
            if not ticker.strip():
                logger.warning("Empty ticker received")
                return TickerAnalysis(ticker=ticker, timeframe=timeframe, error="No ticker provided")

            # Validate timeframe
            normalized_timeframe = timeframe.strip()
            supported_timeframes_lower = [tf.lower() for tf in SUPPORTED_TIMEFRAMES]
            is_supported = normalized_timeframe.lower() in supported_timeframes_lower
            is_quarter = bool(QUARTER_PATTERN.match(normalized_timeframe))
            if not (is_supported or is_quarter):
                logger.warning(f"Unsupported timeframe: '{timeframe}'")
                return TickerAnalysis(
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"Unsupported timeframe; use one of {SUPPORTED_TIMEFRAMES} or 'YYYY QN' (e.g., '2024 Q2')"
                )

            # Validate inputs
            if not news:
                logger.warning("Missing news data")
                return TickerAnalysis(ticker=ticker, timeframe=timeframe, error="Missing news data")
            if not price_change or not price_change.price_change:
                logger.warning("Invalid or missing price change data")
                return TickerAnalysis(ticker=ticker, timeframe=timeframe, error="Invalid or missing price change data")
            if not current_price or not current_price.price:
                logger.warning("Invalid or missing current price data")
                return TickerAnalysis(
                    ticker=ticker,
                    timeframe=timeframe,
                    error="Invalid or missing current price data: expected 'price' with 'current', 'open', 'high', 'low'"
                )

            # Perform sentiment analysis on news
            sentiment = self._analyze_news_sentiment(news)
            
            # Extract price change data
            price_data = price_change.price_change
            absolute_change = price_data.absolute_change
            percentage_change = price_data.percentage_change
            start_price = price_data.start_price
            end_price = price_data.end_price
            
            # Identify key events
            key_events = self._identify_key_events(news, absolute_change, percentage_change, ticker)
            
            # Fetch sector/market data from Finnhub
            sector_data = self._fetch_sector_data(ticker, timeframe)
            
            # Generate summary
            summary = self._generate_summary(ticker, timeframe, sentiment, key_events, price_data, sector_data, current_price)
            
            # Calculate confidence
            confidence = self._calculate_confidence(news, key_events)
            
            analysis = {
                "summary": summary,
                "sentiment": sentiment.dict() if sentiment else None,
                "key_events": [event.dict() for event in key_events] if key_events else [],
                "external_factors": sector_data.get("external_factors", "No external factors identified"),
                "confidence": confidence
            }

            result = TickerAnalysis(
                ticker=ticker,
                analysis=analysis,
                timeframe=timeframe,
                error=None
            )
            logger.info(f"Successfully analyzed {ticker}: {summary}")
            return result

        except Exception as e:
            logger.error(f"Error in analyze_ticker: {str(e)}", exc_info=True)
            return TickerAnalysis(ticker=ticker, timeframe=timeframe, error=f"Analysis failed: {str(e)}")

    def _analyze_news_sentiment(self, news: List[NewsArticle]) -> SentimentAnalysis:
        """Perform sentiment analysis on news articles."""
        positive, negative, neutral = 0, 0, 0
        for article in news:
            headline = article.headline.lower()
            summary = article.summary.lower() if article.summary else ""
            text = headline + " " + summary
            positive_keywords = ["gain", "surge", "rise", "success", "profit", "breakthrough", "strong", "outperform"]
            negative_keywords = ["drop", "decline", "loss", "plummet", "issue", "concern", "weak", "underperform"]
            if any(word in text for word in positive_keywords):
                positive += 1
            elif any(word in text for word in negative_keywords):
                negative += 1
            else:
                neutral += 1
        return SentimentAnalysis(positive=positive, negative=negative, neutral=neutral)

    def _identify_key_events(self, news: List[NewsArticle], absolute_change: float, percentage_change: float, ticker: str) -> List[KeyEvent]:
        """Identify key news events that likely impacted price."""
        key_events = []
        expected_impact = "positive" if percentage_change > 0 else "negative"
        for article in news:
            headline = article.headline.lower()
            published_at = article.published_at
            if isinstance(published_at, datetime):
                published_at = published_at.isoformat()
            impact = "neutral"
            positive_keywords = ["gain", "surge", "rise", "success", "profit", "breakthrough", "strong", "outperform", "buy", "deliveries"]
            negative_keywords = ["drop", "decline", "loss", "plummet", "issue", "concern", "weak", "underperform", "sell"]
            if ticker.lower() in headline or (article.summary and ticker.lower() in article.summary.lower()):
                if any(word in headline for word in positive_keywords):
                    impact = "positive"
                elif any(word in headline for word in negative_keywords):
                    impact = "negative"
                if impact != "neutral" and (impact == expected_impact or abs(percentage_change) > 5):
                    key_events.append(KeyEvent(date=published_at, headline=article.headline, impact=impact))
        logger.debug(f"Identified {len(key_events)} key events for {ticker}")
        return key_events

    def _fetch_sector_data(self, ticker: str, timeframe: str) -> dict:
        """Fetch sector/market context from Finnhub market news for any sector."""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Get company sector
                profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={self.api_key}"
                profile_response = requests.get(profile_url, timeout=5)
                profile_response.raise_for_status()
                profile = profile_response.json()
                sector = profile.get("finnhubIndustry", "Unknown").lower()

                # Define sector keywords
                sector_keywords_map = {
                    "technology": ["technology", "software", "ai", "semiconductor", "tech"],
                    "automobiles": ["automotive", "electric vehicle", "car", "auto"],
                    "financials": ["banking", "finance", "investment", "markets", "financial"],
                    "healthcare": ["healthcare", "pharma", "biotech", "medical"],
                    "energy": ["energy", "oil", "renewable", "gas"],
                    "consumer cyclical": ["retail", "consumer", "e-commerce"],
                    "consumer defensive": ["consumer", "food", "beverage"],
                    "industrials": ["manufacturing", "industrial", "construction"],
                    "basic materials": ["mining", "chemicals", "materials"],
                    "communication services": ["telecom", "media", "internet"],
                    "utilities": ["utilities", "power", "water"],
                    "real estate": ["real estate", "property", "housing"],
                    "unknown": []
                }
                sector_keywords = sector_keywords_map.get(sector, [])

                # Convert timeframe to date range
                if timeframe == "2024 Q2":
                    start_date = "2024-04-01"
                    end_date = "2024-06-30"
                elif timeframe == "2024 Q1":
                    start_date = "2024-01-01"
                    end_date = "2024-03-31"
                elif timeframe == "last week":
                    end_date = datetime.now().strftime("%Y-%m-%d")
                    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                else:
                    logger.warning(f"Unsupported timeframe: {timeframe}")
                    return {"external_factors": f"Unsupported timeframe: {timeframe}"}

                # Fetch company-specific news
                url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={start_date}&to={end_date}&token={self.api_key}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                market_news = response.json()

                # Filter for sector-relevant news
                relevant_news = [
                    news for news in market_news
                    if any(keyword in news.get("headline", "").lower() or keyword in news.get("summary", "").lower()
                           for keyword in sector_keywords) or ticker.lower() in news.get("headline", "").lower()
                ]

                # Fallback to general market news
                if not relevant_news:
                    general_url = f"https://finnhub.io/api/v1/news?category=general&token={self.api_key}"
                    general_response = requests.get(general_url, timeout=5)
                    general_response.raise_for_status()
                    market_news = general_response.json()
                    relevant_news = [
                        news for news in market_news
                        if any(keyword in news.get("headline", "").lower() or keyword in news.get("summary", "").lower()
                               for keyword in sector_keywords)
                    ]

                if relevant_news:
                    latest_news = sorted(relevant_news, key=lambda x: x.get("datetime"), reverse=True)[0]
                    external_factors = f"Market context: {latest_news['headline']} (Source: {latest_news['source']}, {datetime.fromtimestamp(latest_news['datetime']).isoformat()})"
                else:
                    external_factors = f"No relevant {sector} sector news found for {timeframe}"

                return {"external_factors": external_factors}

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error fetching sector data on attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return {"external_factors": "Unable to fetch sector news due to API error"}
            except Exception as e:
                logger.error(f"Error fetching sector data on attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return {"external_factors": "Unable to fetch sector news"}

        return {"external_factors": "Unable to fetch sector news"}

    def _generate_summary(self, ticker: str, timeframe: str, sentiment: SentimentAnalysis, key_events: List[KeyEvent], price_data: PriceChange, sector_data: dict, current_price: TickerPrice) -> str:
        """Generate a summary of price movements."""
        absolute_change = price_data.absolute_change
        percentage_change = price_data.percentage_change
        start_price = price_data.start_price
        end_price = price_data.end_price
        direction = "dropped" if absolute_change < 0 else "rose"
        
        summary = f"{ticker}'s stock {direction} by {abs(percentage_change):.2f}% over the {timeframe}, from ${start_price:.2f} to ${end_price:.2f}. The latest current price is ${current_price.price.current:.2f}."
        
        if key_events:
            summary += " Key events include:"
            for event in key_events[:2]:
                summary += f" On {event.date}, '{event.headline}' had a {event.impact} impact."
        
        if sentiment:
            summary += f" News sentiment shows {sentiment.positive} positive, {sentiment.negative} negative, and {sentiment.neutral} neutral articles."
        
        if sector_data.get("external_factors"):
            summary += f" {sector_data['external_factors']}."
        
        return summary

    def _calculate_confidence(self, news: List[NewsArticle], key_events: List[KeyEvent]) -> float:
        """Calculate confidence based on news volume and relevance."""
        news_count = len(news)
        event_count = len(key_events)
        confidence = min(0.9, 0.5 + (news_count * 0.05) + (event_count * 0.1))
        logger.debug(f"Confidence calculation: news_count={news_count}, event_count={event_count}, confidence={confidence}")
        return round(confidence, 2)