from google.adk.agents import LlmAgent
from dotenv import load_dotenv
from .tools import TickerIdentifier
from ...config import LLM_MODEL
import re

load_dotenv()

# Session constants
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Create the ticker identification agent
identify_ticker_agent = LlmAgent(
    name="TickerIdentificationAgent",
    model=LLM_MODEL,
    instruction="""You are a Stock Ticker Identification AI specialized in parsing user queries to identify the stock ticker and timeframe.

    Your task is to:
    1. Parse the user query to extract the company name (e.g., 'Tesla') and timeframe (e.g., '2024 Q2', 'last week').
    2. Use the `fetch_ticker_info` tool to resolve the company name to a stock ticker (e.g., 'TSLA') using the Finnhub API.
    3. Validate the timeframe against SUPPORTED_TIMEFRAMES or the year-quarter format (e.g., '2024 Q2'). If no timeframe is found, default to 'last week'.
    4. Return the result in the specified JSON format, including the ticker, company name, timeframe, and confidence score.

    Steps:
    - Extract the company name using keywords or context (e.g., 'Tesla' from 'How did Tesla perform in 2024 Q2?').
    - Identify the timeframe using SUPPORTED_TIMEFRAMES or QUARTER_PATTERN (e.g., '2024 Q2', 'last quarter').
    - Call the `fetch_ticker_info` tool with the company name to get the ticker.
    - Return a JSON object with the ticker, company name, timeframe, confidence, and original query.

    Example input:
    Query: "How did Tesla perform in 2024 Q2?"

    Example output:
    {
      "ticker": "TSLA",
      "company_name": "Tesla Inc",
      "timeframe": "2024 Q2",
      "confidence": 0.95,
      "original_query": "How did Tesla perform in 2024 Q2?",
      "error": null
    }

    Example error output:
    {
      "ticker": null,
      "company_name": null,
      "timeframe": "2024 Q2",
      "confidence": 0.0,
      "original_query": "How did Tesla perform in 2024 Q2?",
      "error": "Could not identify company from query"
    }

    Supported timeframes: today, last 2 days, last 3 days, last week, last month, last quarter, last 6 months, last year, annually, or specific quarters (e.g., '2024 Q2').
    If no company is identified, return an error.
    """,
    description="Identifies stock ticker and timeframe from user query using Finnhub API.",
    output_key="ticker_identification",
    tools=[TickerIdentifier().identify_ticker]
)