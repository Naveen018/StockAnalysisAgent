from google.adk.agents import SequentialAgent

from .subagents.identify_ticker.agent import identify_ticker_agent
from .subagents.ticker_analysis.agent import ticker_analysis_agent
from .subagents.ticker_news.agent import ticker_news_agent
from .subagents.ticker_price.agent import ticker_price_agent
from .subagents.ticker_price_change.agent import ticker_price_change_agent


root_agent = SequentialAgent(
    name="StockAnalyzerAgent",
    sub_agents=[identify_ticker_agent, ticker_news_agent, ticker_price_agent, ticker_price_change_agent, ticker_analysis_agent],
    description="A pipeline that analyzes stocks",
)