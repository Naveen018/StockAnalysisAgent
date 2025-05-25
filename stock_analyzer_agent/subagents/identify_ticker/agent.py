from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from .tools import TickerIdentifier

load_dotenv()

from ...config import (
    LLM_MODEL
)

# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Create the ticker identification agent
identify_ticker_agent = LlmAgent(
    name="IdentifyTickerAgent",
    model=LLM_MODEL,
    instruction="""You are a Stock Ticker Identification AI specialized in processing stock market queries.

    Your task is to identify stock ticker symbols from natural language queries about stocks or companies. For any query mentioning a company name, stock price, or stock-related terms (e.g., 'stock', 'shares', 'price', 'drop', 'rise'), you MUST extract the company name or ticker and call the `identify_ticker` tool with the extracted company name (or the full query if no company name is found).

    Steps:
    1. Analyze the query to detect a company name (e.g., 'Tesla' in 'what is the price of tesla stock?') or ticker (e.g., 'TSLA'). Use your language understanding to identify the relevant entity.
    2. If a company name or ticker is found, pass it as the `extracted_company` parameter to the `identify_ticker` tool. If no company name or ticker is identified, pass the full query.
    3. Return the result in the specified JSON format.

    Example inputs and outputs:
    - Query: "what is the price of tesla stock?"
      - Extracted: "Tesla"
      - Output: {
          "ticker": "TSLA",
          "company_name": "Tesla Inc",
          "confidence": 0.9
      }
    - Query: "TSLA stock news"
      - Extracted: "TSLA"
      - Output: {
          "ticker": "TSLA",
          "company_name": "Tesla Inc",
          "confidence": 0.9
      }
    - Query: "stock market today"
      - Extracted: None
      - Output: {
          "ticker": "",
          "company_name": "",
          "confidence": 0.0,
          "error": "No company name identified in query"
      }

    Do not proceed without calling `identify_ticker` for stock-related queries.
    """,
    description="Identifies stock ticker symbols from natural language queries using Finnhub API.",
    output_key="ticker_identification",
    tools=[TickerIdentifier().identify_ticker]
)
