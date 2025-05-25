import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# LLM Configuration
LLM_MODEL = LiteLlm(
    model="openai/gpt-4o-mini",
    api_key=OPENAI_API_KEY,
)

# Session Configuration
APP_NAME = "stock_analyzer_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# API Configuration
POLYGON_BASE_URL = "https://api.polygon.io/v2"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Timeframes
SUPPORTED_TIMEFRAMES = ["today", "daily", "last week", "weekly", "week", "quarterly"] 