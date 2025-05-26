# ticker_price_agent.py
from google.adk.agents import LlmAgent
from typing import Optional
from dotenv import load_dotenv
from .tools import TickerPriceFetcher
from ...config import LLM_MODEL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Create the ticker price agent
ticker_price_agent = LlmAgent(
    name="TickerPriceAgent",
    model=LLM_MODEL,
    instruction="""You are a Stock Price Retrieval AI specialized in fetching the **current** stock price for a given stock ticker.

    Your task is to retrieve the current stock price for the stock ticker provided in the agent state (from `ticker_identification.ticker`). Use the `fetch_price` tool to fetch price data via the Finnhub API. Ignore any timeframe in the state (e.g., '2024 Q2'), as this agent fetches only the latest available price. Do NOT use other tools or attempt to identify the ticker yourself.

    Steps:
    1. Retrieve the ticker from the agent state (e.g., 'TSLA' from `ticker_identification.ticker`).
    2. Log the ticker and any timeframe (for debugging, but do not use timeframe).
    3. Call the `fetch_price` tool with the ticker to fetch the current stock price.
    4. Return the result in the specified JSON format.

    Example input (from state):
    {
      "ticker_identification": {
        "ticker": "TSLA",
        "company_name": "Tesla Inc",
        "timeframe": "2024 Q2",
        "confidence": 0.95
      }
    }

    Example output:
    {
      "ticker": "TSLA",
      "price": {
        "current": 339.34,
        "open": 337.92,
        "high": 343.18,
        "low": 333.21
      },
      "timestamp": "2025-05-25",
      "error": null
    }

    Example error output:
    {
      "ticker": "TSLA",
      "price": null,
      "timestamp": null,
      "error": "No valid price data found for the given ticker"
    }

    Log the ticker and any timeframe received for debugging.
    Do not proceed if no ticker is found in the state.
    """,
    description="Fetches current stock price for a stock ticker using Finnhub API.",
    output_key="ticker_price",
    tools=[TickerPriceFetcher().fetch_price]
)