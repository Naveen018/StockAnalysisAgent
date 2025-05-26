import os
from typing import Optional
from dotenv import load_dotenv
import finnhub
import requests
import json
import logging
import time
import urllib.parse
import re
from ...models import TickerIdentification
from ...config import SUPPORTED_TIMEFRAMES, QUARTER_PATTERN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class TickerIdentifier:
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        self.client = finnhub.Client(api_key=self.api_key)
        logger.info("TickerIdentifier initialized with Finnhub API key")

    def _extract_company_and_timeframe(self, query: str) -> tuple[str, str]:
        """Extract company name and timeframe from the query."""
        query = query.lower().strip()
        company_name = ""
        timeframe = "last week"  # Default timeframe

        # Dictionary of known companies for quick matching
        known_companies = {
            "tesla": "Tesla Inc",
            "apple": "Apple Inc",
            "nvidia": "NVIDIA Corporation",
            "palantir": "Palantir Technologies Inc",
            "microsoft": "Microsoft Corporation",
            "amazon": "Amazon.com Inc",
            "google": "Alphabet Inc",
            "meta": "Meta Platforms Inc"
        }

        # Extract timeframe
        # Check for specific quarter (e.g., "2024 Q2")
        timeframe_match = QUARTER_PATTERN.search(query)
        if timeframe_match:
            timeframe = timeframe_match.group(0)  # e.g., "2024 Q2"
        else:
            # Check for supported relative timeframes
            for tf in SUPPORTED_TIMEFRAMES:
                if tf.lower() in query:
                    timeframe = tf
                    break

        # Extract company name
        # First, try known companies
        for company in known_companies:
            if company in query:
                company_name = known_companies[company]
                break

        # Fallback: extract company name before timeframe or key phrases
        if not company_name:
            # Remove timeframe from query to isolate company
            query_without_timeframe = re.sub(QUARTER_PATTERN, "", query)
            for tf in SUPPORTED_TIMEFRAMES:
                query_without_timeframe = query_without_timeframe.replace(tf.lower(), "")
            # Match company name after phrases like "how did" or "perform"
            match = re.search(r"(?:how did|what’s|perform|stock)\s+([\w\s]+?)(?:\s+in\s+|\s*$)", query_without_timeframe, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip().title()

        logger.info(f"Extracted company: '{company_name}', timeframe: '{timeframe}' from query: '{query}'")
        return company_name, timeframe

    async def identify_ticker(self, query: str, extracted_company: Optional[str] = None) -> TickerIdentification:
        """Identify ticker from the query, using extracted company name if provided."""
        logger.info(f"identify_ticker called with query: {query}, extracted_company: {extracted_company}")
        
        if not query.strip():
            logger.warning("Empty query received")
            return TickerIdentification(
                company_name="",
                ticker="",
                confidence=0.0,
                timeframe="",
                error="No query provided",
                original_query=query
            )

        # Extract company name and timeframe
        search_term, timeframe = self._extract_company_and_timeframe(query) if not extracted_company else (extracted_company, "last week")
        if not search_term.strip():
            logger.warning("No valid company name extracted")
            return TickerIdentification(
                company_name="",
                ticker="",
                confidence=0.0,
                timeframe=timeframe,
                error="No company name identified in query",
                original_query=query
            )

        # Validate timeframe
        if timeframe.lower() not in SUPPORTED_TIMEFRAMES and not QUARTER_PATTERN.match(timeframe):
            logger.warning(f"Invalid timeframe: {timeframe}")
            return TickerIdentification(
                company_name=search_term,
                ticker="",
                confidence=0.0,
                timeframe=timeframe,
                error="Unsupported timeframe; use 'today', 'last 2 days', 'last 3 days', 'last week', 'last month', 'last quarter', 'last 6 months', 'last year', 'annually', or 'YYYY QN' (e.g., '2024 Q2')",
                original_query=query
            )

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Searching Finnhub for company (attempt {attempt}): {search_term}")
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
                        timeframe=timeframe,
                        error="No matching ticker found",
                        original_query=query
                    )

                # Find the best match (prefer common stock)
                best_match = None
                for result in search_results["result"]:
                    if result.get("type") == "Common Stock":
                        best_match = result
                        break
                best_match = best_match or search_results["result"][0]

                ticker = best_match["symbol"]
                company_name = best_match["description"]
                confidence = 0.95 if best_match.get("type") == "Common Stock" else 0.90
                logger.info(f"Best match found - Ticker: {ticker}, Company: {company_name}, Confidence: {confidence}")

                try:
                    logger.info(f"Verifying ticker {ticker} with quote data")
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
                        timeframe=timeframe,
                        error=f"Invalid ticker: {str(e)}",
                        original_query=query
                    )

                result = TickerIdentification(
                    company_name=company_name,
                    ticker=ticker,
                    confidence=confidence,
                    timeframe=timeframe,
                    original_query=query,
                    error=None
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
                        company_name=search_term,
                        ticker="",
                        confidence=0.0,
                        timeframe=timeframe,
                        error="Query not recognized by Finnhub; please use a company name or ticker",
                        original_query=query
                    )
                logger.error(f"HTTP error in identify_ticker on attempt {attempt}: {str(e)}", exc_info=True)
                if attempt < max_retries:
                    logger.info("Retrying after 1-second delay")
                    time.sleep(1)
                    continue
                return TickerIdentification(
                    company_name=search_term,
                    ticker="",
                    confidence=0.0,
                    timeframe=timeframe,
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
                    company_name=search_term,
                    ticker="",
                    confidence=0.0,
                    timeframe=timeframe,
                    error=f"Failed after {max_retries} attempts: {str(e)}",
                    original_query=query
                )