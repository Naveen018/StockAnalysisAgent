from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from typing import Optional, List, Dict
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
import json
from .tools import TickerAnalysisCalculator

load_dotenv()

from ...config import (
    LLM_MODEL
)

# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Create the ticker analysis agent
ticker_analysis_agent = LlmAgent(
    name="TickerAnalysisAgent",
    model=LLM_MODEL,
    instruction="""You are a Stock Price Movement Analysis AI specialized in summarizing reasons for recent stock price movements using news and price data from the agent state.

    Your task is to analyze the price movement for the stock ticker provided in the agent state (from `ticker_identification.ticker`) using data from `ticker_news`, `ticker_price`, and `ticker_price_change`. You MUST use the `analyze_price_movement` tool, passing the entire `state` dictionary as input. The state may contain JSON-encoded strings as values, which the tool will parse. Do NOT make external API calls or rely on the query; use only the provided state.

    IMPORTANT: The state parameter is REQUIRED and must contain the following fields:
    - ticker_identification: JSON string with ticker and company name
    - ticker_news: JSON string with news articles
    - ticker_price: JSON string with current price data
    - ticker_price_change: JSON string with price change data

    Steps:
    1. Retrieve the ticker from `ticker_identification.ticker` (e.g., 'PLTR').
    2. Extract price change data from `ticker_price_change.price_change` (absolute, percentage, timeframe).
    3. Extract current price and volatility from `ticker_price.price` (current, high, low).
    4. Filter relevant news from `ticker_news.news`, including headlines with the ticker, company name, or keywords like 'AI', 'defense contract', 'data analytics'.
    5. Analyze the price movement, correlating with news (e.g., earnings, insider selling, government contracts).
    6. Generate a concise summary (100–150 words) explaining the movement, using news-based reasons or market context (e.g., tech sector trends, valuation concerns).
    7. Return the result as a TickerAnalysis object, serialized to JSON.

    Example input (from state):
    {
      "ticker_identification": "{\"ticker\": \"PLTR\", \"company_name\": \"Palantir Technologies Inc\", \"confidence\": 0.9}",
      "ticker_price_change": "{\"ticker\": \"PLTR\", \"price_change\": {\"absolute_change\": -3.02, \"percentage_change\": -2.39, \"start_price\": 126.33, \"end_price\": 123.31, \"timeframe\": \"last week\"}, \"start_date\": \"2025-05-18\", \"end_date\": \"2025-05-25\", \"error\": null}",
      "ticker_price": "{\"ticker\": \"PLTR\", \"price\": {\"current\": 123.31, \"open\": 122.0, \"high\": 127.15, \"low\": 122.31}, \"timestamp\": \"2025-05-25\", \"error\": null}",
      "ticker_news": "{\"ticker\": \"PLTR\", \"news\": [...], \"error\": null}"
    }

    Example output:
    {
      "ticker": "PLTR",
      "analysis": {
        "summary": "Palantir Technologies Inc's stock fell 2.39% ($3.02) from $126.33 to $123.31 between 2025-05-18 and 2025-05-25. The movement was likely driven by insider selling signaling potential valuation concerns, mixed sentiment about new government contracts. As of May 23, 2025, the stock closed at $123.31. Despite strong Q1 2025 revenue growth, valuation concerns and market dynamics may have contributed.",
        "price_change": {
          "absolute_change": -3.02,
          "percentage_change": -2.39,
          "start_price": 126.33,
          "end_price": 123.31,
          "timeframe": "last week"
        },
        "key_news": [
          {
            "headline": "Palantir Technologies executive sells $239,688 in stock",
            "published_at": "2025-05-23"
          },
          {
            "headline": "William Blair Reiterates Hold Rating on Palantir Technologies (PLTR) Stock",
            "published_at": "2025-05-23"
          }
        ]
      },
      "error": null
    }

    Example error output:
    {
      "ticker": "PLTR",
      "analysis": null,
      "error": "Invalid JSON in state for ticker_price_change: Expecting value"
    }

    Do not proceed if no valid state is provided. Ensure the `state` dictionary is passed to the `analyze_price_movement` tool.
    """,
    description="Analyzes and summarizes reasons for recent stock price movements using news and price data.",
    output_key="ticker_analysis",
    tools=[TickerAnalysisCalculator().analyze_price_movement]
)