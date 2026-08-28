---
agent: agent-datacommons
---

# agent datacommons

> [!note]
> for agent runtime (reasoning engine) & 3p public mcp server

data commons mcp server
- https://docs.datacommons.org/mcp/run_tools.html

> [!warning]
> need to create data commons account (free) to get an api key
> - https://apikeys.datacommons.org/

> [!important]
> add api key as env var for deploying to agent

```sh
# set api key env var
 export DC_API_KEY="YOUR_API_KEY_HERE"
```

## setup

```sh
# set new vars
export RE_AGENT_NAME="agent-datacommons"
export MCP_URL="https://api.datacommons.org/mcp"
echo ${RE_AGENT_NAME}
echo ${MCP_URL}
```

> [!note]
> these vars below should be the same as what just set up in [`agw-egress-public.md`](./agw-egress-public.md#setup)... just repeating here if refresh needed

```sh
# re-set old vars (if needed)
export SLUG="baz"
export REGION="europe-west4"
export MREGION="eu"
echo ${SLUG}
echo ${REGION}
echo ${MREGION}
```

```sh
# re-fetch old vars (if needed)
export PROJ_ID=$(gcloud config list --format="value(core.project)")
export PROJ_NO=$(gcloud projects describe ${PROJ_ID} --format="value(projectNumber)")
export ORG_ID=$(gcloud projects get-ancestors ${PROJ_ID} --format="value(id)" | tail -n 1)
echo ${PROJ_ID}
echo ${PROJ_NO}
echo ${ORG_ID}
```

```sh
# re-make old vars (if needed)
export AGW_NAME="agw-${SLUG}-${REGION}-ata"
export AGW_URI="projects/${PROJ_ID}/locations/${REGION}/agentGateways/${AGW_NAME}"
export RE_AGENT_NAME="agent-datacommons"
export RE_AGENT_ID_SET="principalSet://agents.global.org-${ORG_ID}.system.id.goog/attribute.platformContainer/aiplatform/projects/${PROJ_NO}"
export STAGING_BUCKET="agent-staging-${PROJ_NO}"
echo ${AGW_NAME}
echo ${AGW_URI}
echo ${RE_AGENT_NAME}
echo ${RE_AGENT_ID_SET}
echo ${STAGING_BUCKET}
```

## storage

```sh
# create bucket for agent code staging (if does not exist)
gcloud storage buckets create gs://${STAGING_BUCKET} --project=${PROJ_ID} --location=${REGION}
```

```sh
# check bucket urls
gcloud storage buckets list --format="value(storage_url)"
```

## registry

```sh
# generate toolspec for registry
uv --directory agent-datacommons run python3 test_mcp.py --toolspec=include --token="${DC_API_KEY}"
```

> [!note]
> add mcp server to registry manually...

```sh
# register mcp server
gcloud alpha agent-registry services create datacommons-mcp \
  --project=${PROJ_ID} \
  --location=${REGION} \
  --display-name="api.datacommons.org" \
  --description="mcp server for data commons" \
  --mcp-server-spec-type=tool-spec \
  --mcp-server-spec-content=agent-datacommons/toolspec.json \
  --interfaces=url=${MCP_URL},protocolBinding=JSONRPC
```

```sh
# list registry mcp servers
gcloud alpha agent-registry mcp-servers list --project=${PROJ_ID} --location=${REGION} --format="table(displayName, interfaces.url)"
```

## deploy re

```sh
# deploy re agent
uv --directory agent-datacommons run python3 deploy_agent.py \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --src-dir=./agent \
  --staging-bucket=${STAGING_BUCKET} \
  --display-name="${RE_AGENT_NAME}" \
  --description="agent for data commons stats" \
  --enable-telemetry \
  --enable-agent-identity \
  --agent-gateway-egress=${AGW_URI} \
  --env-var="DC_API_KEY=${DC_API_KEY}"
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

> for ge app (if/when used later)

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

> ask about some data commons things... "what data do you have on water quality in zimbabwe?"

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
    httpRequest.requestUrl.trailoff(101):label=URL
  )'
```

## setup ge

> [!note]
> these vars below should be the same as what just set up in [`agw-egress-public.md`](./agw-egress-public.md#ge-app)... just repeating here if refresh needed

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
  "description": "provides statistical and factual information about places, demographics, health indicators, and economics by querying data commons",
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "this agent specializes in retrieving public statistics and factual data from the data commons knowledge graph. it should be invoked for any user queries related to statistics, demographics, geographic data, health indicators, or economic benchmarks. this agent can answer questions like what data do you have on water quality in zimbabwe?, what is the population of california?, what is the gdp of france?, etc. do not use this agent for general queries or information not typically found in public statistical databases."
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
> go back to [`agw-egress-public.md`](./agw-egress-public.md#test-dry-run) to continue...
