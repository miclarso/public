---
agent: agent-qotd
---

# agent qotd

> [!note]
> for agent runtime (reasoning engine) & www server

## setup

> [!important]
> env vars reused from [`agw-egress-vpc.md`](./agw-egress-vpc.md#setup)

```sh
# new vars
export ENDPOINT_URL="http://qotd.${SLUG}.lab"
echo ${ENDPOINT_URL}
```

## storage

```sh
# check existing buckets
gcloud storage buckets list --format="value(storage_url)"
```

```sh
# create bucket for agent code staging
gcloud storage buckets create gs://${STAGING_BUCKET} --project=${PROJ_ID} --location=${REGION}
```

```sh
# check bucket urls
gcloud storage buckets list --format="value(storage_url)"
```

## www server

```sh
# create startup file
cat > cfg/startup-www.sh << REALEOF
#! /bin/bash
# GCP Startup Script: Quote of the Day Web Server

# 1. Create the Python web server script
cat << 'EOF' > /opt/quote_server.py
import http.server
import socketserver
import random

QUOTES = [
    "The computer was born to solve problems that did not exist before.",
    "Talk is cheap. Show me the code. - Linus Torvalds",
    "Programs must be written for people to read, and only incidentally for machines to execute. - Harold Abelson",
    "Truth can only be found in one place: the code. - Robert C. Martin",
    "It's not a bug. It's an undocumented feature."
]

class QuoteHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Respond with 200 OK and plain text headers
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        
        # Select a random quote and send it
        quote = random.choice(QUOTES) + "\n"
        self.wfile.write(quote.encode("utf-8"))

if __name__ == "__main__":
    # Bind to all interfaces on port 80
    with socketserver.TCPServer(("", 80), QuoteHandler) as httpd:
        httpd.serve_forever()
EOF

# 2. Create the systemd service file
cat << 'EOF' > /etc/systemd/system/quote-server.service
[Unit]
Description=Quote of the Day HTTP Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/quote_server.py
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# 3. Reload systemd, enable, and start the service
systemctl daemon-reload
systemctl enable quote-server.service
systemctl start quote-server.service
REALEOF
```

```sh
# create vm instance
gcloud compute instances create vm-www \
  --zone=${ZONE} \
  --machine-type=e2-micro \
  --subnet=subnet-${SLUG}-${REGION}-2 \
  --no-address \
  --private-network-ip=10.128.2.99 \
  --scopes=cloud-platform \
  --shielded-secure-boot \
  --metadata-from-file=startup-script=cfg/startup-www.sh
```

```sh
# test www
gcloud compute ssh vm-www --zone=${ZONE} \
  --command="curl -s http://qotd.${SLUG}.lab"
```

## registry

> [!note]
> add qotd www endpoint to registry manually...

```sh
# register endpoint
gcloud alpha agent-registry services create www-${SLUG}-qotd \
  --project=${PROJ_ID} \
  --location=${REGION} \
  --display-name="qotd.${SLUG}.lab" \
  --endpoint-spec-type=no-spec \
  --interfaces="url=${ENDPOINT_URL},protocolBinding=HTTP_JSON"
```

```sh
# verify registry endpoint (regional) by display name
gcloud alpha agent-registry endpoints list \
  --project=${PROJ_ID} \
  --location=${REGION} \
  --filter="displayName=qotd.${SLUG}.lab" \
  --format="table(displayName, name.basename():label=ENDPOINT_ID, interfaces[0].url:label=URL)"
```

```sh
# describe registry service (endpoint) by name
gcloud alpha agent-registry services describe www-${SLUG}-qotd \
  --project=${PROJ_ID} \
  --location=${REGION}
```

## deploy re

```sh
# deploy re agent
uv --directory agent-qotd run python3 deploy_agent.py \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --src-dir=./agent \
  --staging-bucket=${STAGING_BUCKET} \
  --display-name="${RE_AGENT_NAME}" \
  --description="agent for quotes of the day" \
  --enable-telemetry \
  --enable-agent-identity \
  --agent-gateway-egress=${AGW_URI} \
  --endpoint-url=${ENDPOINT_URL}
```

```sh
# fetch re engine id
export RE_ENGINE_ID=$(curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  | jq -r --arg name "${RE_AGENT_NAME}" '.reasoningEngines[] | select(.displayName==$name) | .name | split("/") | last')
echo ${RE_ENGINE_ID}
```

```sh
# verify re agent identity and gateway config
curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  | jq '{displayName: .displayName, name: .name, effectiveIdentity: .spec.effectiveIdentity, agentGatewayConfig: .spec.deploymentSpec.agentGatewayConfig}'
```

```sh
# fetch re agent identity
export RE_AGENT_IDENTITY=$(gcloud alpha agent-registry agents list \
  --project=${PROJ_ID} --location=${REGION} --filter="displayName=${RE_AGENT_NAME}" \
  --format="value(attributes.'agentregistry.googleapis.com/system/RuntimeIdentity'.principal)")
echo ${RE_AGENT_IDENTITY}
```

## iam

> for re agent

```sh
# show agent identity roles on project
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${RE_AGENT_IDENTITY}" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=IDENTITY)"
```

> [!note]
> no role bindings on agent identity at this point

```sh
# show agent set roles on project
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${RE_AGENT_ID_SET}" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=IDENTITY)"
```

> for ge app

```sh
# grant role aiplatform user to discovery engine sa
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="serviceAccount:service-${PROJ_NO}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

```sh
# show discovery engine sa roles on project
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:service-${PROJ_NO}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=IDENTITY)"
```

## re test

> [!note]
> jump to console

```sh
# playground
echo "https://console.cloud.google.com/agent-platform/runtimes/locations/${REGION}/agent-engines/${RE_ENGINE_ID}/playground?project=${PROJ_ID}"
```

> ask for quote... "what is the quote of the day?"

> [!tip]
> check logs...

```sh
# show gateway logs (requests w/ urls)
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=10 \
  --format='table(
    timestamp.date(tz=LOCAL):label=TIMESTAMP,
    httpRequest.requestMethod:label=METHOD,
    httpRequest.status:label=STATUS,
    jsonPayload.authzPolicyInfo.result:label=IAP_AUTHZ,
    jsonPayload.agentGatewayInfo.mcpInfo.method:label=MCP_METHOD,
    httpRequest.requestUrl.trailoff(123):label=URL
  )'
```

## setup ge

```sh
# set vars
export GE_LOCATION="global"
export GE_APP_NAME="app-${SLUG}-${GE_LOCATION}"
echo ${GE_LOCATION}
echo ${GE_APP_NAME}
```

```sh
# list discovery engine instances (ge apps)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" | jq '.engines[]? | {displayName: .displayName, name: .name}'
```

```sh
# fetch ge app id
export GE_APP_ID=$(curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq -r --arg name "${GE_APP_NAME}" '.engines[] | select(.displayName==$name) | .name | split("/") | last')
echo ${GE_APP_ID}
```

> [!note]
> register re agent with ge... post to engine (ge app) level

```sh
# register re agent with discovery engine instance (ge app)
curl -X POST "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
-d @- <<EOF
{
  "displayName": "${RE_AGENT_NAME}",
  "description": "provides quotes of the day",
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "this agent specializes in retrieving quotes of the day. it should be invoked for any user queries related to quotes or sayings. this agent can answer questions like what is the quote of the day?, etc. do not use this agent for general queries or information not related to quotes, sayings, quips, aphorisms, proverbs, etc."
    },
    "provisioned_reasoning_engine": {
      "reasoning_engine": "projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}"
    }
  }
}
EOF
```

```sh
# show agent registered to discovery engine instance (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" | jq -r --arg name "${RE_AGENT_NAME}" '.agents[] | select(.displayName==$name)'
```

> [!note]
> enable observability on ge app... patch to engine (ge app) level

```sh
# set observability on discovery engine instance (ge app)
curl -X PATCH "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}?updateMask=observabilityConfig" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" \
-d @- <<EOF
{
  "observabilityConfig": {
    "observabilityEnabled": true,
    "sensitiveLoggingEnabled": true
  }
}
EOF
```

```sh
# show config for discovery engine instance (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" | jq .
```

## return

> [!warning]
> go back to [`agw-egress-vpc.md`](./agw-egress-vpc.md#test-dry-run) to continue...
