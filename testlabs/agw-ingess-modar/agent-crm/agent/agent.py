"""Agent CRM - Customer GCS Data Retrieval Agent.

Version: v1.2.0
Last Updated: 2026-06-03T09:40:00-04:00

Changelog:
- v1.2.0 (2026-06-03): Reverted urllib3 pyopenssl monkeypatching to prevent ValueError context reuse crashes during background telemetry exports.
- v1.1.0 (2026-06-02): Changed GCS default fallback GCS bucket to 'cloud-samples-data' to ensure a valid, publicly accessible default is available for testing.
- v1.0.0 (2026-06-02): Initial agent-crm template creation for reasoning engine deployment.
"""

import os
import logging
import time
from urllib.parse import urlparse

# Revert pyopenssl monkeypatching in urllib3 to prevent ValueError on SSL Context reuse
try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.extract_from_urllib3()
except Exception:
    pass
from google.adk.agents import LlmAgent
import httpx
import json
import uuid

logger = logging.getLogger("agent_crm")
logging.basicConfig(level=logging.INFO)

async def log_identity():
    """Fetch and log the identity from the metadata server."""
    try:
        async with httpx.AsyncClient() as client:
            # Query the default service account email from metadata server
            response = await client.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email",
                headers={"Metadata-Flavor": "Google"},
                timeout=2.0
            )
            if response.status_code == 200:
                logger.info(f"Metadata Server Identity: {response.text.strip()}")
            else:
                logger.warning(f"Metadata server returned status {response.status_code} for identity check.")
    except Exception as e:
        logger.warning(f"Could not fetch identity from metadata server: {e}")

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Helper to call Google-managed MCP server via plain HTTP POST."""
    url = os.getenv("MCP_URL")
    if not url:
        raise ValueError("MCP_URL environment variable not set.")
        
    # Log the active principal identity
    await log_identity()
        
    # Fetch Access Token dynamically at runtime using standard ADC
    token = os.getenv("ACCESS_TOKEN")
    if not token:
        try:
            import google.auth
            import google.auth.transport.requests
            
            credentials, project = google.auth.default()
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            token = credentials.token
            logger.info("Successfully refreshed standard Access Token via ADC.")
        except Exception as e:
            logger.warning(f"Could not fetch Access Token via ADC: {e}")
            
    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": str(uuid.uuid4()),
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    logger.info(f"MCP Call Initiation | Tool: '{tool_name}' | Target URL: {url} | Arguments: {json.dumps(arguments)}")
    
    start_time = time.perf_counter()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            elapsed = time.perf_counter() - start_time
            
            if response.status_code != 200:
                logger.error(f"MCP Call Failed | Tool: '{tool_name}' | Status: {response.status_code} | Latency: {elapsed:.3f}s | Details: {response.text}")
                return f"Error: MCP server returned {response.status_code}"
                
            resp_json = response.json()
            if "error" in resp_json:
                logger.error(f"MCP Call JSON-RPC Error | Tool: '{tool_name}' | Latency: {elapsed:.3f}s | Error Details: {json.dumps(resp_json['error'])}")
                return f"MCP Error: {resp_json['error'].get('message')}"
                
            result = resp_json.get("result", {})
            content_list = result.get("content", [])
            text_out = "No text response received."
            for content in content_list:
                if content.get("type") == "text":
                    text_out = content.get("text")
                    break
                    
            logger.info(f"MCP Call Success | Tool: '{tool_name}' | Latency: {elapsed:.3f}s | Response size: {len(text_out)} chars")
            return text_out
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"MCP Call Exception | Tool: '{tool_name}' | Latency: {elapsed:.3f}s | Error: {e}")
            return f"Error: {e}"

# Define tools manually, mapping to camelCase arguments expected by the server
async def list_objects(bucket_name: str, prefix: str = "", recursive: bool = False) -> str:
    """List objects in a Google Cloud Storage bucket.

    Args:
        bucket_name: The name of the bucket.
        prefix: Filter results to objects whose names begin with this prefix.
        recursive: Whether to list recursively.
    """
    return await call_mcp_tool("list_objects", {"bucketName": bucket_name, "prefix": prefix, "recursive": recursive})

async def read_text(bucket_name: str, object_name: str) -> str:
    """Read non-binary text content from an object in a Google Cloud Storage bucket.

    Args:
        bucket_name: The name of the bucket.
        object_name: The name of the object.
    """
    return await call_mcp_tool("read_text", {"bucketName": bucket_name, "objectName": object_name})

data_bucket = os.getenv("DATA_BUCKET", "cloud-samples-data")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent_crm",
    description="An agent to fetch google cloud storage data using mcp",
    instruction=f"""You are the "Customer Data Retrieval Agent," a highly specialized assistant whose ONLY purpose is to answer questions by retrieving and analyzing data from Google Cloud Storage (GCS).

YOUR SCOPE AND CAPABILITIES:
1. You have access to a Google Cloud Storage MCP server. You must use the tools provided by this server (such as [list_objects] and [read_text]) to fulfill user requests.
2. The user will frequently refer to "customer data." Whenever the user asks about "customer data" or "sample data," you must look in this specific GCS path: gs://{data_bucket}/
3. You are a precise data fetcher. This is your only specialty.

OPERATING RULES (STRICT):
- Always use your GCS MCP tools to look up information. Do not rely on your internal training data to answer questions about the customer data.
- If a user asks a question, first list the objects in gs://{data_bucket}/ to find the relevant file, then read the file contents, and finally answer the user's question based strictly on that text.
- If the answer cannot be found in the files within that bucket, you must respond: "I cannot find that information in the customer data bucket." Do not guess.
- Refuse any request to perform tasks outside of reading and summarizing data from this specific GCS bucket (e.g., do not write code, do not tell jokes, do not browse the web).""",
    tools=[list_objects, read_text],
)
