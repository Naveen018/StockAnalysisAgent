from google.adk.agents import SequentialAgent
import logging

from .subagents.identify_ticker.agent import identify_ticker_agent
from .subagents.ticker_analysis.agent import ticker_analysis_agent
from .subagents.ticker_news.agent import ticker_news_agent
from .subagents.ticker_price.agent import ticker_price_agent
from .subagents.ticker_price_change.agent import ticker_price_change_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

root_agent = SequentialAgent(
    name="StockAnalyzerAgent",
    sub_agents=[identify_ticker_agent, ticker_news_agent, ticker_price_agent, ticker_price_change_agent, ticker_analysis_agent],
    description="A pipeline that analyzes stocks",
)


async def run_root_agent(query: str, state: dict = None) -> dict:
    """Run the sequential agent pipeline with explicit state management."""
    if state is None:
        state = {}
    logger.info(f"Starting query: '{query}' with initial state: {state}")
    for subagent in root_agent.subagents:
        logger.info(f"Executing subagent: {subagent.name} with output_key: {subagent.output_key}")
        try:
            # Execute subagent and update state
            subagent_output = await subagent.run(query=query, state=state.copy())
            state[subagent.output_key] = subagent_output
            logger.info(f"Subagent {subagent.name} output: {subagent_output}")
        except Exception as e:
            logger.error(f"Error in subagent {subagent.name}: {str(e)}", exc_info=True)
            state[subagent.output_key] = {"error": f"Subagent failed: {str(e)}"}
    logger.info(f"Final state: {state}")
    return state