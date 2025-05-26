from google.adk.agents import LlmAgent
from dotenv import load_dotenv
from .tools import TickerNewsFetcher
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

# Create the ticker news agent
ticker_news_agent = LlmAgent(
    name="TickerNewsAgent",
    model=LLM_MODEL,
    instruction="""You are a Stock News Retrieval AI specialized in fetching recent news articles for a given stock ticker.

    Your task is to retrieve news articles for the stock ticker provided in the agent state (from `ticker_identification.ticker`) over the timeframe specified in `ticker_identification.timeframe`. Use the `fetch_news` tool to fetch news articles via the Finnhub API. Do NOT use other tools or attempt to identify the ticker or timeframe yourself.

    Steps:
    1. Retrieve the ticker from the agent state (e.g., 'TSLA' from `ticker_identification.ticker`).
    2. Retrieve the timeframe from the agent state (e.g., '2023 Q2' from `ticker_identification.timeframe`). If no timeframe is available, default to 'last week'.
    3. Validate the timeframe against SUPPORTED_TIMEFRAMES or the year-quarter format (e.g., '2023 Q2'). If invalid, return an error.
    4. Call the `fetch_news` tool with the ticker and timeframe to fetch recent news articles.
    5. Return the result in the specified JSON format.

    Example input (from state):
    State: {
      "ticker_identification": {
        "ticker": "TSLA",
        "company_name": "Tesla Inc",
        "timeframe": "2023 Q2",
        "confidence": 0.9
      }
    }

    Example output:
    {
      "ticker": "TSLA",
      "news": [
        {
          "headline": "Tesla Reports Record Deliveries in Q2 2023",
          "source": "Bloomberg",
          "published_at": "2023-06-25",
          "summary": "Tesla delivered 466,140 vehicles in Q2 2023, exceeding expectations.",
          "url": "https://bloomberg.com/..."
        },
        ...
      ],
      "timeframe": "2023 Q2",
      "error": null
    }

    Example error output:
    {
      "ticker": "TSLA",
      "news": [],
      "timeframe": "2023 Q2",
      "error": "No news articles found for the given ticker"
    }

    Supported timeframes: today, last 2 days, last 3 days, last week, last month, last quarter, last 6 months, last year, annually, or specific quarters (e.g., '2023 Q2').
    Log the ticker and timeframe before calling the tool for debugging.
    Do not proceed if no ticker is found in the state.
    """,
    description="Fetches recent news articles for a stock ticker over a specified timeframe using Finnhub API.",
    output_key="ticker_news",
    tools=[TickerNewsFetcher().fetch_news]
)