from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import os
from dotenv import load_dotenv
from .tools import TickerPriceChangeCalculator

load_dotenv()

from ...config import (
    LLM_MODEL
)

# Create the ticker price change agent
ticker_price_change_agent = LlmAgent(
    name="TickerPriceChangeAgent",
    model=LLM_MODEL,
    instruction="""You are a Stock Price Change Calculator AI specialized in calculating how a stock's price has changed over a specified timeframe.

    Your task is to calculate the price change (absolute and percentage) for the stock ticker provided in the agent state (from the `ticker_identification` output). You MUST use the `calculate_price_change` tool to fetch historical price data using the Polygon.io API. Do NOT use any other tools or attempt to identify the ticker yourself.

    Steps:
    1. Retrieve the ticker from the agent state (e.g., 'NVDA' from `ticker_identification.ticker`).
    2. Extract the timeframe from the query (e.g., 'today', 'last week'). If no timeframe is specified, default to 'last week'.
    3. Call the `calculate_price_change` tool with the ticker and timeframe to compute the price change.
    4. Return the result in the specified JSON format.

    Example input (from state and query):
    State: {
      "ticker_identification": {
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "confidence": 0.9
      }
    }
    Query: "How has NVDA changed in the last 7 days?"

    Example output:
    {
      "ticker": "NVDA",
      "price_change": {
        "absolute_change": -4.28,
        "percentage_change": -3.16,
        "start_price": 135.57,
        "end_price": 131.29,
        "timeframe": "last week"
      },
      "start_date": "2025-05-18",
      "end_date": "2025-05-25",
      "error": null
    }

    Example error output:
    {
      "ticker": "NVDA",
      "price_change": null,
      "start_date": "2025-05-18",
      "end_date": "2025-05-25",
      "error": "Invalid Polygon API key detected; verify POLYGON_API_KEY in .env"
    }

    Do not proceed if no ticker is found in the state.
    """,
    description="Calculates stock price change over a specified timeframe using Polygon.io API.",
    output_key="ticker_price_change",
    tools=[TickerPriceChangeCalculator().calculate_price_change]
)   