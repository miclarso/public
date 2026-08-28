# LICENSE HEADER

# Version 1.6.0

import os
from google.adk.agents import LlmAgent
from google.cloud import storage

data_bucket = os.getenv("DATA_BUCKET", "cloud-samples-data")


def list_customer_files() -> str:
    """Lists all customer data files available in the secure GCS bucket.

    Returns:
        A newline-separated list of filenames found in the customer data bucket.
    """
    client = storage.Client()
    bucket = client.bucket(data_bucket)
    blobs = list(bucket.list_blobs())
    return "\n".join(blob.name for blob in blobs) if blobs else "No files found in customer data bucket."


def read_customer_file(file_name: str) -> str:
    """Reads the content of a specific customer data file from Google Cloud Storage.

    Args:
        file_name: The name of the file in the bucket (e.g. 'customers_vip.csv').

    Returns:
        The text content of the file.
    """
    client = storage.Client()
    bucket = client.bucket(data_bucket)
    blob = bucket.blob(file_name)
    if not blob.exists():
        return f"File '{file_name}' not found in customer data bucket."
    return blob.download_as_text()


# Build the Agent
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent_crm",
    description="An agent to fetch customer data securely via native Google Cloud Storage SDK over mTLS",
    instruction=f"""You are the "Customer Data Retrieval Agent," a highly specialized assistant whose ONLY purpose is to answer questions by retrieving and analyzing data from Google Cloud Storage (GCS).

YOUR SCOPE AND CAPABILITIES:
1. You have secure access to Cloud Storage via native tools ([list_customer_files] and [read_customer_file]) to fulfill user requests.
2. Whenever the user asks about "customer data" or "sample data," you must look in GCS bucket: {data_bucket}
3. You are a precise data fetcher. This is your only specialty.

OPERATING RULES (STRICT):
- Always use your storage tools to look up information. Do not rely on your internal training data to answer questions about the customer data.
- If a user asks a question, first list the objects in the GCS bucket using [list_customer_files] to find the relevant file, then read the file contents using [read_customer_file], and finally answer the user's question based strictly on that text.
- If the answer cannot be found in the GCS bucket, you must respond: "I cannot find that information in the customer data bucket." Do not guess.
- Refuse any request to perform tasks outside of reading and summarizing GCS data (e.g., do not write code, do not tell jokes, do not browse the web).""",
    tools=[list_customer_files, read_customer_file],
)
