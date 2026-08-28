---
agent: agent-dj
---

# agent dj

> [!note]
> for agent runtime (reasoning engine) & gcloud mcp server

## setup

```sh
# set vars
export SLUG="foo"
export REGION="us-east1"
export MREGION="us"
echo ${SLUG}
echo ${REGION}
echo ${MREGION}
```

```sh
# fetch vars
export PROJ_ID=$(gcloud config list --format="value(core.project)")
export PROJ_NO=$(gcloud projects describe ${PROJ_ID} --format="value(projectNumber)")
export ORG_ID=$(gcloud projects get-ancestors ${PROJ_ID} | awk '$2 == "organization" {print $1}')
echo ${PROJ_ID}
echo ${PROJ_NO}
echo ${ORG_ID}
```

```sh
# new vars
export RE_AGENT_NAME="agent-dj"
export RE_AGENT_ID_SET="principalSet://agents.global.org-${ORG_ID}.system.id.goog/attribute.platformContainer/aiplatform/projects/${PROJ_NO}"
export STAGING_BUCKET="agent-staging-${PROJ_NO}"
export AGW_URI="projects/${PROJ_ID}/locations/${REGION}/agentGateways/${AGW_NAME}"
echo ${RE_AGENT_NAME}
echo ${RE_AGENT_ID_SET}
echo ${STAGING_BUCKET}
echo ${AGW_URI}
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

## bigquery

```sh
# ingest table to bq dataset
bq --project_id=${PROJ_ID} query \
  --use_legacy_sql=false < agent-dj/setup.sql
```

## deploy re

```sh
# deploy re agent
uv --directory agent-dj run python3 deploy_agent.py \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --src-dir=./agent \
  --staging-bucket=${STAGING_BUCKET} \
  --display-name="${RE_AGENT_NAME}" \
  --description="agent for dj contact info" \
  --enable-telemetry \
  --enable-agent-identity \
  --agent-gateway-egress=${AGW_URI} \
  --allow-token-sharing
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
# grant role bigquery user to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${RE_AGENT_IDENTITY}" \
  --role="roles/bigquery.user"

# grant role bigquery data viewer to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${RE_AGENT_IDENTITY}" \
  --role="roles/bigquery.dataViewer"

# grant role mcp tool user to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${RE_AGENT_IDENTITY}" \
  --role="roles/mcp.toolUser"

# grant role aiplatform user to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${RE_AGENT_IDENTITY}" \
  --role="roles/aiplatform.user"
```

```sh
# show agent identity roles on project
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${RE_AGENT_IDENTITY}" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=IDENTITY)"
```

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

> ask about some dj contact things... "what are all the dj names we have on file?"

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

> [!caution]
> if need to delete...

```sh
# delete agent
curl -X DELETE "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}?force=true" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json"
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
  "description": "provides realtime information about djs, including phone and credit card numbers, by querying a live database",
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "this agent specializes in retrieving live data about djs from a bigquery database. it should be invoked for any user queries related to dj contact information (namely phone numbers and credit card numbers), as well as anything related to using music disc jockey services. this agent can answer questions like what is dj x's phone number?, how many djs do we have working with us?, what is dj x's credit card number?, etc. do not use this agent for general music queries or information not typically stored in a dj management database."
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
> go back to [`agw-egress-gmcp.md`](../agw-egress-gmcp.md#test-dry-run) to continue...
