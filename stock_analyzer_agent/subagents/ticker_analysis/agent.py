from google.adk.agents import LlmAgent
from typing import List
from pydantic import ValidationError
from dotenv import load_dotenv
from .tools import TickerAnalyzer
from ...config import LLM_MODEL, FINNHUB_API_KEY
from ...models import NewsArticle, TickerPriceChange, TickerPrice, TickerAnalysis, TickerIdentification, TickerNews
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Create the ticker analysis agent
ticker_analysis_agent = LlmAgent(
    name="TickerAnalysisAgent",
    model=LLM_MODEL,
    instruction="""You are a Stock Analysis AI specialized in analyzing and summarizing reasons behind stock price movements using news and historical price data.

    Your task is to analyze the stock ticker provided in the agent state (from `ticker_identification.ticker`) using data from `ticker_news`, `ticker_price`, and `ticker_price_change`. Use the `analyze_ticker` tool to perform sentiment analysis on news, correlate price changes, and identify external factors (e.g., market or sector trends) using the Finnhub API.

    Steps:
    1. Retrieve the ticker, news, current price, and price change data from the agent state.
    2. Extract the timeframe from `ticker_price_change.timeframe` or `ticker_identification.timeframe`. Default to 'last week' if unavailable.
    3. Validate inputs and convert to Pydantic models:
       - ticker: str from `state.ticker_identification.ticker`
       - timeframe: str from `state.ticker_price_change.timeframe` or `state.ticker_identification.timeframe`
       - news: List[NewsArticle] from `state.ticker_news.news`, converting datetime fields to strings
       - price_change: TickerPriceChange from `state.ticker_price_change`
       - current_price: TickerPrice from `state.ticker_price`
    4. Call the `analyze_ticker` tool with the validated inputs.
    5. Generate a summary explaining price movements, linking to specific news events, and suggesting external factors.
    6. Assign a confidence score based on the volume and relevance of news articles.
    7. Return the result in the specified JSON format.

    Example input (from state):
    {
      "ticker_identification": {
        "ticker": "TSLA",
        "company_name": "Tesla Inc",
        "timeframe": "2024 Q2",
        "confidence": 0.95
      },
      "ticker_news": {
        "ticker": "TSLA",
        "news": [
          {
            "headline": "Tesla Breaks Out with Strong Q2 Deliveries",
            "source": "Yahoo",
            "published_at": "2024-06-30T00:00:00",
            "summary": "Tesla reported record deliveries in Q2 2024.",
            "url": "https://finance.yahoo.com/..."
          },
          ...
        ],
        "timeframe": "2024 Q2"
      },
      "ticker_price": {
        "ticker": "TSLA",
        "price": {
          "current": 339.34,
          "open": 337.92,
          "high": 343.18,
          "low": 333.21
        },
        "timestamp": "2025-05-25",
        "error": null
      },
      "ticker_price_change": {
        "ticker": "TSLA",
        "price_change": {
          "absolute_change": 22.66,
          "percentage_change": 12.93,
          "start_price": 175.22,
          "end_price": 197.88,
          "timeframe": "2024 Q2"
        },
        "start_date": "2024-04-01",
        "end_date": "2024-06-30",
        "error": null
      }
    }

    Example output:
    {
      "ticker": "TSLA",
      "analysis": {
        "summary": "Tesla's stock rose by 12.93% in Q2 2024, from $175.22 to $197.88. The latest current price is $339.34...",
        "sentiment": {"positive": 4, "negative": 1, "neutral": 5},
        "key_events": [
          {
            "date": "2024-06-30T00:00:00",
            "headline": "Tesla Breaks Out with Strong Q2 Deliveries",
            "impact": "positive"
          },
          ...
        ],
        "external_factors": "Market context: Automotive sector sees EV growth (Source: Reuters, 2024-06-30)",
        "confidence": 0.87
      },
      "timeframe": "2024 Q2",
      "error": null
    }

    Log the ticker, timeframe, and input data availability for debugging.
    Ensure datetime fields (e.g., published_at) are strings in ISO format.
    Do not proceed if no ticker or insufficient data is found in the state.""",
    description="Analyzes reasons behind stock price movements using news, price data, and sector trends.",
    output_key="ticker_analysis",
    tools=[TickerAnalyzer().analyze_ticker]
)