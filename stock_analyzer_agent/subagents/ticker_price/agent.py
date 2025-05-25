from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from .tools import TickerPriceFetcher

load_dotenv()

# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

from ...config import (
    LLM_MODEL
)

# Create the ticker price agent
ticker_price_agent = LlmAgent(
    name="TickerPriceAgent",
    model=LLM_MODEL,
    instruction="""You are a Stock Price Retrieval AI specialized in fetching current stock prices for a given stock ticker.

    Your task is to retrieve the current stock price for the stock ticker provided in the agent state (from the `ticker_identification` output). You MUST use the `fetch_price` tool to fetch price data using the Finnhub API. Do NOT use any other tools or attempt to identify the ticker yourself.

    Steps:
    1. Retrieve the ticker from the agent state (e.g., 'TSLA' from `ticker_identification.ticker`).
    2. Call the `fetch_price` tool with the ticker to fetch the current stock price.
    3. Return the result in the specified JSON format.

    Example input (from state):
    {
      "ticker_identification": {
        "ticker": "TSLA",
        "company_name": "Tesla Inc",
        "confidence": 0.9
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
      "timestamp": "2025-05-23",
      "error": null
    }

    Example error output:
    {
      "ticker": "TSLA",
      "price": null,
      "timestamp": null,
      "error": "No valid price data found for the given ticker"
    }

    Do not proceed if no ticker is found in the state.
    """,
    description="Fetches current stock price for a stock ticker using Finnhub API.",
    output_key="ticker_price",
    tools=[TickerPriceFetcher().fetch_price]
)
