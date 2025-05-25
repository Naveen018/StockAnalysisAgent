from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import finnhub
import requests
import json
import logging
import time
import urllib.parse
from ...models import TickerIdentification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Ticker Identifier Logic ---
class TickerIdentifier:
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        self.client = finnhub.Client(api_key=self.api_key)
        logger.info("TickerIdentifier initialized with Finnhub API key")

    async def identify_ticker(self, query: str, extracted_company: Optional[str] = None) -> TickerIdentification:
        """Identify ticker from the query provided by the LLM, using extracted company name."""
        logger.info(f"identify_ticker called with query: {query}, extracted_company: {extracted_company}")
        
        if not query.strip():
            logger.warning("Empty query received")
            return TickerIdentification(
                company_name="",
                ticker="",
                confidence=0.0,
                error="No query provided",
                original_query=query
            )

        # Use extracted company name if provided, else fall back to query
        search_term = extracted_company if extracted_company else query
        if not search_term.strip():
            logger.warning("No valid company name extracted")
            return TickerIdentification(
                company_name="",
                ticker="",
                confidence=0.0,
                error="No company name identified in query",
                original_query=query
            )

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Searching Finnhub for company (attempt {attempt}): {search_term}")
                # Use Finnhub's /v1/search endpoint
                encoded_query = urllib.parse.quote(search_term)
                url = f"https://finnhub.io/api/v1/search?q={encoded_query}&token={self.api_key}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                search_results = response.json()
                logger.info(f"Finnhub search results: {json.dumps(search_results, indent=2)}")

                if not search_results.get("result") or len(search_results["result"]) == 0:
                    logger.warning(f"No matches found in Finnhub on attempt {attempt}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerIdentification(
                        company_name=search_term,
                        ticker="",
                        confidence=0.0,
                        error="No matching ticker found",
                        original_query=query
                    )

                best_match = search_results["result"][0]
                ticker = best_match["symbol"]
                company_name = best_match["description"]
                # Finnhub search doesn't provide a confidence score; assume high confidence for first result
                confidence = 0.9
                logger.info(f"Best match found - Ticker: {ticker}, Company: {company_name}, Confidence: {confidence}")

                try:
                    logger.info(f"Verifying ticker {ticker} with quote data")
                    # Verify ticker with Finnhub quote endpoint
                    quote = self.client.quote(ticker)
                    if quote.get("c", 0) == 0:
                        raise ValueError("No valid quote data for ticker")
                    logger.info("Ticker verification successful")
                except Exception as e:
                    logger.error(f"Ticker verification failed: {str(e)}")
                    return TickerIdentification(
                        company_name=company_name,
                        ticker="",
                        confidence=0.0,
                        error=f"Invalid ticker: {str(e)}",
                        original_query=query
                    )

                result = TickerIdentification(
                    company_name=company_name,
                    ticker=ticker,
                    confidence=confidence,
                    original_query=query
                )
                logger.info(f"Successfully identified ticker: {result}")
                return result
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 422:
                    logger.error(f"Unprocessable query on attempt {attempt}: {str(e)}")
                    if attempt < max_retries:
                        logger.info("Retrying after 1-second delay")
                        time.sleep(1)
                        continue
                    return TickerIdentification(
                        company_name="",
                        ticker="",
                        confidence=0.0,
                        error="Query not recognized by Finnhub; please use a company name or ticker",
                        original_query=query
                    )
                logger.error(f"HTTP error in identify_ticker on attempt {attempt}: {str(e)}", exc_info=True)
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerIdentification(
                    company_name="",
                    ticker="",
                    confidence=0.0,
                    error=f"Failed after {max_retries} attempts: {str(e)}",
                    original_query=query
                )
            except Exception as e:
                logger.error(f"Error in identify_ticker on attempt {attempt}: {str(e)}", exc_info=True)
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerIdentification(
                    company_name="",
                    ticker="",
                    confidence=0.0,
                    error=f"Failed after {max_retries} attempts: {str(e)}",
                    original_query=query
                )