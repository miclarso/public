---
agent: agent-crm
---

# agent crm

> [!note]
> for agent runtime (reasoning engine) & gcloud mcp server

## setup

```sh
# set vars
export SLUG="tc2"
export AGW_NAME="agw-${SLUG}-cta"
export REGION="us-west1"
echo ${SLUG}
echo ${AGW_NAME}
echo ${REGION}
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
export AGENT_NAME="agent-crm"
export AGENT_SA_SET="principalSet://agents.global.org-${ORG_ID}.system.id.goog/attribute.platformContainer/aiplatform/projects/${PROJ_NO}"
export STAGING_BUCKET="agent-staging-${PROJ_NO}"
export DATA_BUCKET="customer-data-${PROJ_NO}"
export AGW_URI="projects/${PROJ_ID}/locations/${REGION}/agentGateways/${AGW_NAME}"
export MCP_URL="https://storage.googleapis.com/storage/mcp"
echo ${AGENT_NAME}
echo ${AGENT_SA_SET}
echo ${STAGING_BUCKET}
echo ${DATA_BUCKET}
echo ${AGW_URI}
echo ${MCP_URL}
```

## storage

```sh
# check existing buckets
gcloud storage buckets list --format="value(storage_url)"
```

```sh
# create bucket for crm agent code staging
gcloud storage buckets create gs://${STAGING_BUCKET} --project=${PROJ_ID} --location=${REGION}

# create bucket for crm data
gcloud storage buckets create gs://${DATA_BUCKET} --project=${PROJ_ID} --location=${REGION}

# check bucket urls
gcloud storage buckets list --format="value(storage_url)"
```

```sh
# upload customer data
gcloud storage cp -r ./agent-crm/data/* gs://${DATA_BUCKET}/

# check bucket objects
gcloud storage ls gs://${DATA_BUCKET}/ --long
```

## deploy

```sh
# deploy agent
uv --directory agent-crm run python3 deploy_agent.py \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --src-dir=./agent \
  --staging-bucket=${STAGING_BUCKET} \
  --display-name="${AGENT_NAME}" \
  --description="agent to fetch crm data from gcs using mcp" \
  --mcp-server-url="${MCP_URL}" \
  --data-bucket=${DATA_BUCKET} \
  --enable-telemetry \
  --enable-agent-identity \
  --agent-gateway-ingress=${AGW_URI}
```

```sh
# fetch engine id
export ENGINE_ID=$(curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  | jq -r --arg name "${AGENT_NAME}" '.reasoningEngines[] | select(.displayName==$name) | .name' \
  | awk -F/ '{print $NF}')
echo ${ENGINE_ID}
```

```sh
# verify agent identity and gateway config
curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${ENGINE_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  | jq '{displayName: .displayName, name: .name, effectiveIdentity: .spec.effectiveIdentity, agentGatewayConfig: .spec.deploymentSpec.agentGatewayConfig}'
```

```sh
# fetch agent identity
export AGENT_IDENTITY=$(gcloud alpha agent-registry agents list \
  --project=${PROJ_ID} --location=${REGION} --filter="displayName=${AGENT_NAME}" \
  --format="value(attributes.'agentregistry.googleapis.com/system/RuntimeIdentity'.principal)")
echo ${AGENT_IDENTITY}
```

## iam

```sh
# grant role storage object viewer to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${AGENT_IDENTITY}" \
  --role="roles/storage.objectViewer"

# grant role aiplatform user to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${AGENT_IDENTITY}" \
  --role="roles/aiplatform.user"

# grant role cloudtrace agent to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${AGENT_IDENTITY}" \
  --role="roles/cloudtrace.agent"

# grant role cloud monitoring metric writer to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${AGENT_IDENTITY}" \
  --role="roles/monitoring.metricWriter"

# grant role cloud logging log writer to agent identity
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${AGENT_IDENTITY}" \
  --role="roles/logging.logWriter"
```

```sh
# grant role mcp tool user to agent set (all project agents)
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="${AGENT_SA_SET}" \
  --role="roles/mcp.toolUser"
```

```sh
# show agent identity roles on project
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${AGENT_IDENTITY}" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=IDENTITY)"

# show agent set roles on project
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${AGENT_SA_SET}" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=IDENTITY_SET)"
```

## test

> [!note]
> jump to console

```sh
# go to playground (echo url to click)
echo "https://console.cloud.google.com/agent-platform/runtimes/locations/${REGION}/agent-engines/${ENGINE_ID}/playground?project=${PROJ_ID}"
```

> ask about some customer data

```sh
# check logs
gcloud logging read \
  "textPayload:\"MCP Call\" OR jsonPayload.message:\"MCP Call\"" \
  --limit=10 \
  --format='table(
    timestamp.date(format="%I:%M:%S %p", tz=LOCAL):label=TIME,
    textPayload.trailoff(172):label=TEXT
  )'
```

> [!caution]
> if need to delete...

```sh
# delete agent
curl -X DELETE "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${ENGINE_ID}?force=true" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json"
```

## return

> [!important]
> return to [`agw-ingress-modar.md`](../agw-ingress-modar.md#test) to continue...
