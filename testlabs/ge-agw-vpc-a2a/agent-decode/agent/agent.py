import os
import uuid
import logging
import json
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-decode")

app = FastAPI(title="agent-decode", version="1.0.1")

# Agent Card Definition
AGENT_CARD = {
    "name": "agent-decode",
    "description": "agent for a2a protocol response",
    "url": os.getenv("AGENT_A2A_URL", "example.com/agent-decode"),
    "version": "1.0.1",
    "defaultInputModes": ["text/plain", "application/json"],
    "defaultOutputModes": ["text/plain", "application/json"],
    "capabilities": {
        "streaming": False
    },
    "skills": [
        {
            "id": "request_decoder",
            "name": "Request Decoder",
            "description": "Decodes and prints out all HTTP and A2A protocol characteristics including method, headers, parameters, and raw JSON payload.",
            "tags": ["diagnostic", "decoder", "protocol", "a2a"],
            "examples": [
                "Send any request to agent-decode to inspect the A2A protocol details and JSON payload."
            ]
        }
    ]
}

def extract_text_from_payload(payload: Dict[str, Any]) -> str:
    """Extract input text from JSON-RPC or REST payload if available."""
    try:
        if "params" in payload and isinstance(payload["params"], dict):
            params = payload["params"]
            if "message" in params and isinstance(params["message"], dict):
                parts = params["message"].get("parts", [])
                for part in parts:
                    if isinstance(part, dict) and "text" in part:
                        return part["text"]
        if "message" in payload and isinstance(payload["message"], dict):
            parts = payload["message"].get("parts", [])
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    return part["text"]
    except Exception as e:
        logger.warning(f"Error parsing input text: {e}")
    return str(payload.get("text", payload.get("prompt", "N/A")))

def decode_request_characteristics(request: Request, payload: Dict[str, Any], raw_body: str) -> str:
    """Formats all HTTP and A2A protocol characteristics into a readable text report."""
    headers_dict = dict(request.headers)
    query_params = dict(request.query_params)
    
    rpc_jsonrpc = payload.get("jsonrpc", "N/A") if isinstance(payload, dict) else "N/A"
    rpc_id = payload.get("id", "N/A") if isinstance(payload, dict) else "N/A"
    rpc_method = payload.get("method", "N/A") if isinstance(payload, dict) else "N/A"
    rpc_params = payload.get("params", None) if isinstance(payload, dict) else None
    
    extracted_text = extract_text_from_payload(payload) if isinstance(payload, dict) else "N/A"
    
    try:
        formatted_payload = json.dumps(payload, indent=2) if isinstance(payload, dict) and payload else (raw_body or "{}")
    except Exception:
        formatted_payload = raw_body or str(payload)

    lines = [
        "=== A2A Request Decoder Characteristics ===",
        "",
        "[HTTP Request Details]",
        f"Method: {request.method}",
        f"URL: {str(request.url)}",
        f"Path: {request.url.path}",
        f"Client Host: {request.client.host if request.client else 'unknown'}",
        f"Query Parameters: {json.dumps(query_params)}",
        "",
        "[HTTP Headers]",
    ]
    for k, v in sorted(headers_dict.items()):
        lines.append(f"  {k}: {v}")
        
    lines.extend([
        "",
        "[A2A Protocol Details]",
        f"JSON-RPC Version (jsonrpc): {rpc_jsonrpc}",
        f"Request ID (id): {rpc_id}",
        f"Protocol Method (method): {rpc_method}",
        f"Extracted Input Text: {extracted_text}",
        "",
        "[A2A Parameters (params)]",
        json.dumps(rpc_params, indent=2) if rpc_params is not None else "None",
        "",
        "[Full JSON Payload]",
        formatted_payload
    ])
    
    return "\n".join(lines)

def build_a2a_response(request_id: Optional[Any], response_text: str) -> Dict[str, Any]:
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    context_id = f"ctx-{uuid.uuid4().hex[:8]}"
    msg_id = f"msg-{uuid.uuid4().hex[:8]}"
    artifact_id = f"art-{uuid.uuid4().hex[:8]}"
    res_id = request_id if request_id is not None else f"req-{uuid.uuid4().hex[:8]}"
    
    return {
        "jsonrpc": "2.0",
        "id": res_id,
        "result": {
            "id": task_id,
            "contextId": context_id,
            "status": {
                "state": "completed"
            },
            "history": [
                {
                    "messageId": msg_id,
                    "role": "agent",
                    "parts": [
                        {
                            "kind": "text",
                            "text": response_text
                        }
                    ]
                }
            ],
            "artifacts": [
                {
                    "artifactId": artifact_id,
                    "name": "decode_response",
                    "parts": [
                        {
                            "kind": "text",
                            "text": response_text
                        }
                    ]
                }
            ]
        }
    }

@app.get("/")
@app.get("/agent.json")
@app.get("/.well-known/agent.json")
async def get_agent_card():
    return JSONResponse(content=AGENT_CARD)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def handle_a2a_request(request: Request, path: str):
    # Handle agent card GET requests at any path prefix
    if request.method == "GET" and (path.endswith("agent.json") or path == "" or path == ".well-known/agent.json"):
        return JSONResponse(content=AGENT_CARD)

    raw_body = ""
    try:
        body_bytes = await request.body()
        raw_body = body_bytes.decode("utf-8")
        payload = json.loads(raw_body) if raw_body else {}
    except Exception:
        payload = {}

    request_id = payload.get("id") if isinstance(payload, dict) else None
    
    decoded_summary = decode_request_characteristics(request, payload, raw_body)
    logger.info(f"Decoded request from {request.client.host if request.client else 'unknown'}:\n{decoded_summary}")
    
    response_data = build_a2a_response(request_id, decoded_summary)
    return JSONResponse(content=response_data)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
