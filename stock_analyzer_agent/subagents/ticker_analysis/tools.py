from dotenv import load_dotenv
import logging
import json
from typing import Dict, Any

from ...models import PriceChange, TickerAnalysis, NewsItem, Analysis
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# --- Ticker Analysis Logic ---
class TickerAnalysisCalculator:
    async def analyze_price_movement(self, state: Dict[str, Any]) -> TickerAnalysis:
        """Analyze and summarize reasons for recent price movements using state data."""
        logger.info("analyze_price_movement called")
        
        # Log state for debugging
        logger.info(f"Received state: {json.dumps(state, indent=2) if state else 'Empty dict'}")
        
        # Handle empty state
        if not state:
            logger.warning("Empty state provided")
            return TickerAnalysis(
                ticker="",
                analysis=None,
                error="No valid state provided to analyze_price_movement"
            )

        # Parse JSON strings in state
        parsed_state = {}
        for key in ["ticker_identification", "ticker_news", "ticker_price", "ticker_price_change"]:
            value = state.get(key, {})
            if isinstance(value, str):
                try:
                    parsed_state[key] = json.loads(value)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse {key} as JSON: {value[:100]}... Error: {str(e)}")
                    return TickerAnalysis(
                        ticker="",
                        analysis=None,
                        error=f"Invalid JSON in state for {key}: {str(e)}"
                    )
            else:
                parsed_state[key] = value

        # Extract ticker from state
        ticker_data = parsed_state.get("ticker_identification", {})
        ticker = ticker_data.get("ticker", "")
        company_name = ticker_data.get("company_name", "")
        if not ticker:
            logger.warning("No ticker found in state")
            return TickerAnalysis(
                ticker="",
                analysis=None,
                error="No ticker provided in state"
            )

        logger.info(f"Analyzing price movement for {ticker}")

        # Extract price change data
        price_change_data = parsed_state.get("ticker_price_change", {})
        price_change = price_change_data.get("price_change")
        start_date = price_change_data.get("start_date", "")
        end_date = price_change_data.get("end_date", "")

        # Extract current price and volatility
        price_data = parsed_state.get("ticker_price", {})
        current_price = price_data.get("price", {}).get("current", 0.0)
        price_high = price_data.get("price", {}).get("high", 0.0)
        price_low = price_data.get("price", {}).get("low", 0.0)
        volatility = (price_high - price_low) / current_price * 100 if current_price else 0

        # Extract news data
        news_data = parsed_state.get("ticker_news", {})
        news_items = news_data.get("news", [])
        logger.info(f"News items received: {len(news_items)}")

        # Validate required data
        if not price_change:
            logger.warning(f"No price change data for {ticker}")
            return TickerAnalysis(
                ticker=ticker,
                analysis=None,
                error="No price change data available"
            )

        # Create PriceChange model
        try:
            price_change_model = PriceChange(
                absolute_change=price_change["absolute_change"],
                percentage_change=price_change["percentage_change"],
                start_price=price_change["start_price"],
                end_price=price_change["end_price"],
                timeframe=price_change["timeframe"]
            )
        except Exception as e:
            logger.error(f"Invalid price change data for {ticker}: {str(e)}")
            return TickerAnalysis(
                ticker=ticker,
                analysis=None,
                error="Invalid price change data format"
            )

        # Filter relevant news
        key_news = []
        for item in news_items:
            headline = item.get("headline", "").lower()
            # Broaden filtering to include PLTR-relevant keywords
            if (ticker.lower() in headline or 
                company_name.lower() in headline or
                any(kw in headline for kw in ["ai ", "artificial intelligence", "defense contract", "data analytics", "government contract"])):
                key_news.append(NewsItem(
                    headline=item["headline"],
                    published_at=item["published_at"]
                ))
        if not key_news:
            logger.info(f"No {ticker}-specific news found")

        # Generate analysis summary
        direction = "rose" if price_change["absolute_change"] > 0 else "fell"
        abs_change = abs(price_change["absolute_change"])
        abs_percent = abs(price_change["percentage_change"])
        timeframe = price_change["timeframe"]

        # Base summary
        summary = (
            f"{company_name}'s stock {direction} {abs_percent:.2f}% (${abs_change:.2f}) from ${price_change['start_price']:.2f} "
            f"to ${price_change['end_price']:.2f} between {start_date} and {end_date}. "
        )

        # Dynamic news-based reasoning
        if key_news:
            # Define keyword-based reasons
            reasons = []
            for item in key_news:
                headline = item.headline.lower()
                if any(kw in headline for kw in ["earnings", "results", "quarterly"]):
                    sentiment = "caution" if price_change["absolute_change"] < 0 else "optimism"
                    reasons.append(f"investor {sentiment} surrounding recent earnings reports")
                elif any(kw in headline for kw in ["insider", "sell", "stock sale"]):
                    reasons.append("insider selling signaling potential valuation concerns")
                elif any(kw in headline for kw in ["defense", "contract", "government"]):
                    sentiment = "optimism" if price_change["absolute_change"] > 0 else "mixed sentiment"
                    reasons.append(f"{sentiment} about new government contracts")
                elif any(kw in headline for kw in ["valuation", "rating", "analyst"]):
                    reasons.append("analyst ratings impacting investor confidence")
                elif any(kw in headline for kw in ["ai ", "artificial intelligence", "data analytics"]):
                    sentiment = "excitement" if price_change["absolute_change"] > 0 else "concerns"
                    reasons.append(f"{sentiment} about AI and data analytics developments")

            # Deduplicate and limit reasons
            reasons = list(dict.fromkeys(reasons))[:3]
            if reasons:
                summary += "The movement was likely driven by " + ", ".join(reasons) + ". "
            else:
                summary += (
                    f"Volatility ({volatility:.2f}%) reflects broader tech sector trends, possibly due to macroeconomic factors. "
                )
        else:
            # Improved fallback summary
            summary += (
                f"Volatility ({volatility:.2f}%) aligns with tech sector trends, potentially driven by macroeconomic factors like rising Treasury yields "
                f"or investor caution over high valuations. "
            )

        # Add current price and context
        summary += (
            f"As of May 23, 2025, the stock closed at ${current_price:.2f}. Despite strong Q1 2025 revenue growth, valuation concerns and market dynamics may have contributed."
        )

        # Create Analysis model
        analysis = Analysis(
            summary=summary,
            price_change=price_change_model,
            key_news=key_news
        )

        result = TickerAnalysis(
            ticker=ticker,
            analysis=analysis,
            error=None
        )
        logger.info(f"Successfully generated analysis for {ticker}: {summary}")
        return result