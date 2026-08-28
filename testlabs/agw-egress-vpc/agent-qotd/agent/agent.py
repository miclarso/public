import os
import logging
from google.adk.agents import LlmAgent

# Revert pyopenssl monkeypatching in urllib3 to prevent ValueError on SSL Context reuse
try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.extract_from_urllib3()
except Exception:
    pass

logger = logging.getLogger("agent_qotd")
logging.basicConfig(level=logging.INFO)

async def get_quote_of_the_day() -> str:
    """Fetch the Quote of the Day from the configured endpoint.

    Returns:
        The text content of the quote of the day.
    """
    import httpx
    
    endpoint = os.getenv("ENDPOINT_URL")
    if not endpoint:
        endpoint = "http://qotd.default.lab"
        logger.warning(f"ENDPOINT_URL not set in environment. Falling back to {endpoint}")

    logger.info(f"Fetching Quote of the Day from: {endpoint}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, timeout=10.0)
            if response.status_code == 200:
                logger.info("Successfully fetched Quote of the Day.")
                return response.text
            else:
                logger.error(f"Failed to fetch quote. HTTP status: {response.status_code}")
                return f"Error: Received status code {response.status_code} from quote server."
    except Exception as e:
        logger.error(f"Error calling quote server: {e}")
        return f"Error connecting to quote server: {e}"

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent_qotd",
    description="An agent to retrieve the Quote of the Day.",
    instruction=(
        "You are the 'Quote of the Day' assistant. Your sole purpose is to retrieve "
        "and present the Quote of the Day (sometimes referred to as qotd) to the user. "
        "Always use the `get_quote_of_the_day` tool to fetch the quote when requested. "
        "Do not make up quotes or try to answer questions outside of this scope."
    ),
    tools=[get_quote_of_the_day],
)
