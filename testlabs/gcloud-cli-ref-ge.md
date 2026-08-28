# gcloud cli reference

for gemini enterprise (discovery engine)

## discovery engine

## org policy

### custom mcp

```sh
# describe effective org policy (at org level)
gcloud org-policies describe constraints/discoveryengine.managed.disableCustomMcpServerConnector --organization=${ORG_ID} --effective
```

```sh
# describe effective org policy (at project level)
gcloud org-policies describe constraints/discoveryengine.managed.disableCustomMcpServerConnector --project=${PROJ_ID} --effective
```

```sh
# disable enforcement (at project level)
gcloud org-policies set-policy /dev/stdin << EOF
name: projects/${PROJ_ID}/policies/discoveryengine.managed.disableCustomMcpServerConnector
spec:
  rules:
  - enforce: false
EOF
```

```sh
# verify org policy (at project level)
gcloud org-policies describe constraints/discoveryengine.managed.disableCustomMcpServerConnector --project=${PROJ_ID} --effective
```

```sh
# enable enforcement (at project level)
gcloud org-policies set-policy /dev/stdin << EOF
name: projects/${PROJ_ID}/policies/discoveryengine.managed.disableCustomMcpServerConnector
spec:
  rules:
  - enforce: true
EOF
```

```sh
# remove project override and inherit org default
gcloud org-policies reset constraints/discoveryengine.managed.disableCustomMcpServerConnector --project=${PROJ_ID}
```

### egress fqdn

```sh
# describe effective allowed egress fqdns policy (at org level)
gcloud org-policies describe constraints/discoveryengine.managed.allowedEgressFqdns --organization=${ORG_ID} --effective
```

```sh
# describe effective allowed egress fqdns policy (at project level)
gcloud org-policies describe constraints/discoveryengine.managed.allowedEgressFqdns --project=${PROJ_ID} --effective
```

```sh
# allow specific fqdns for connector egress (at project level)
gcloud org-policies set-policy /dev/stdin << EOF
name: projects/${PROJ_ID}/policies/discoveryengine.managed.allowedEgressFqdns
spec:
  rules:
  - enforce: true
    parameters:
      allowedEgressFqdns:
      - "ai.todoist.net"
      - "todoist.com"
EOF
```

> [!caution]
> disables the constraint entirely to allow access to all external domains

```sh
# disable egress fqdn enforcement completely (at project level)
gcloud org-policies set-policy /dev/stdin << EOF
name: projects/${PROJ_ID}/policies/discoveryengine.managed.allowedEgressFqdns
spec:
  rules:
  - enforce: false
EOF
```

```sh
# verify allowed fqdns policy (at project level)
gcloud org-policies describe constraints/discoveryengine.managed.allowedEgressFqdns --project=${PROJ_ID}
```

```sh
# remove project override and inherit org default (at project level)
gcloud org-policies reset constraints/discoveryengine.managed.allowedEgressFqdns --project=${PROJ_ID}
```

## iam

### gateway

> [!note]
> for routing to gateway

```sh
# set vars
export PRINCIPAL_USER="EMAIL_ADDRESS"
echo ${PRINCIPAL_USER}
```

```sh
# show roles granted to user principal on project
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${PRINCIPAL_USER}" \
  --format="table(bindings.role)"
```

> [!note]
> for registry actions (grant permission to discovery engine sa)

```sh
# create custom role
gcloud iam roles create AgentGatewayRouting \
  --project=${PROJ_ID} \
  --title="agent gateway and registry ops" \
  --description="custom role for agent gateway and registry ops for routing" \
  --permissions="agentregistry.agents.list,agentregistry.agents.search,agentregistry.agents.get,agentregistry.mcpServers.list,agentregistry.mcpServers.search,agentregistry.mcpServers.get,networkservices.agentGateways.list,networkservices.agentGateways.get,networkservices.agentGateways.use"
```

```sh
# verify custom role permissions
gcloud iam roles describe AgentGatewayRouting --project=${PROJ_ID}
```

```sh
# grant the custom role to discovery engine (ge) sa
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="serviceAccount:service-${PROJ_NO}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --role="projects/${PROJ_ID}/roles/AgentGatewayRouting"
```

```sh
# verfiy iam binding on discovery engine (ge) sa
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:service-${PROJ_NO}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=IDENTITY)"
```

### users

```sh
# show users with ge app access
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.role:(roles/discoveryengine.agentspaceUser roles/discoveryengine.user roles/discoveryengine.agentspaceAdmin roles/discoveryengine.admin roles/discoveryengine.viewer)" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=USER_OR_GROUP)"
```

## ge app

```sh
# set vars
export SLUG="foo"
export GE_LOCATION="global"
export GE_APP_NAME="app-${SLUG}-${GE_LOCATION}"
echo ${SLUG}
echo ${GE_LOCATION}
echo ${GE_APP_NAME}
```

```sh
# create random app id
export GE_APP_ID="${GE_APP_NAME}_$(python3 -c 'import time; print(int(time.time() * 1000))')"
echo ${GE_APP_ID}
```

```sh
# create ge app (discovery engine)
curl -X POST "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines?engineId=${GE_APP_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "displayName": "${GE_APP_NAME}",
  "dataStoreIds": [],
  "solutionType": "SOLUTION_TYPE_SEARCH",
  "industryVertical": "GENERIC",
  "appType": "APP_TYPE_INTRANET",
  "searchEngineConfig": {
    "searchTier": "SEARCH_TIER_ENTERPRISE",
    "searchAddOns": [
      "SEARCH_ADD_ON_LLM"
    ]
  },
  "knowledgeGraphConfig": {
    "enablePrivateKnowledgeGraph": true
  },
  "features": {
    "disable-agent-sharing": "FEATURE_STATE_OFF",
    "enable-end-user-sharing-with-groups": "FEATURE_STATE_OFF",
    "agent-sharing-without-admin-approval": "FEATURE_STATE_ON"
  },
  "marketplaceAgentVisibility": "SHOW_ALL_AGENTS"
}
EOF
```

```sh
# list discovery engine instances (ge apps)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" | jq '.engines[]? | {displayName: .displayName, name: .name}'
```

```sh
# fetch discovery engine instance (ge app) id
export GE_APP_ID=$(curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq -r --arg name "${GE_APP_NAME}" '.engines[] | select(.displayName==$name) | .name | split("/") | last')
echo ${GE_APP_ID}
```

```sh
# show config for discovery engine instance (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" | jq .
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

### data connectors

```sh
# list data connectors
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/dataConnector" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" | jq .
```

### data stores

```sh
# list datastores linked to discovery engine (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" | jq '.dataStoreIds'
```

```sh
# set vars
export GE_DS_NAME="saas-foo-global"
echo ${GE_DS_NAME}
```

```sh
# fetch datastore id
export GE_DS_ID=$(curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq -r --arg name "${GE_DS_NAME}" '.dataStoreIds[] | select(startswith($name))')
echo ${GE_DS_ID}
```

```sh
# show datastore configuration
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/dataStores/${GE_DS_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" | jq .
```

### agents

#### custom agents

```sh
# list all agents registered with discovery engine (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq '.agents[]? | {displayName: .displayName, name: .name}'
```

#### re agent

```sh
# register reasoning engine agent with discovery engine (ge app)
curl -X POST "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  -d @- <<EOF
{
  "displayName": "${RE_AGENT_NAME}",
  "description": "${RE_AGENT_DESC}",
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "${RE_AGENT_TOOL_DESC}"
    },
    "provisioned_reasoning_engine": {
      "reasoning_engine": "projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}"
    }
  }
}
EOF
```

```sh
# get (list) custom reasoning engine agents registered with discovery engine (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq '.agents[]? | select(.adkAgentDefinition.provisionedReasoningEngine != null) | {displayName: .displayName, reasoningEngine: .adkAgentDefinition.provisionedReasoningEngine.reasoningEngine, name: .name}'
```

```sh
RE_AGENT_NAME="agent-weather"
echo ${RE_AGENT_NAME}
```

```sh
# show discovery engine agent config for ${RE_AGENT_NAME}
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq --arg name "${RE_AGENT_NAME}" '.agents[] | select(.displayName==$name)'
```

```sh
# extract registered discovery engine agent resource id
export GE_CUSTOM_AGENT_ID=$(curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq -r --arg name "${RE_AGENT_NAME}" '.agents[] | select(.displayName==$name) | .name | split("/") | last')
echo ${GE_CUSTOM_AGENT_ID}
```

#### a2a agent

```sh
# get (list) all a2a [custom and manually imported] agents registered with discovery engine (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq '.agents[]? | select(.a2aAgentDefinition != null) | {displayName: .displayName, importedAgent: .importedAgent.agent, name: .name}'
```

```sh
A2A_AGENT_NAME="agent-decode"
echo ${A2A_AGENT_NAME}
```

```sh
# show discovery engine agent config for ${A2A_AGENT_NAME}
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq --arg name "${A2A_AGENT_NAME}" '.agents[] | select(.displayName==$name)'
```

#### system agents

```sh
# get (list) all default system agents [automatically] registered with discovery engine (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq '.agents[]? | select(.managedAgentDefinition != null) | {displayName: .displayName, importedAgent: .importedAgent.agent, name: .name}'
```


#### low code

aka "employee-made"

```sh
# get (list) all low code ("employee-made") agents registered with discovery engine (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq '.agents[]? | select(.lowCodeAgentDefinition != null) | {displayName: .displayName, agentId: (.name | split("/") | last), agentType: "Employee-made", name: .name}'
```


#### agent registry

```sh
# import a2a agent to discovery engine (ge app) from agent registry
curl -X POST "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  -d @- << EOF
{
  "displayName": "${A2A_AGENT_NAME}",
  "description": "${DESCRIPTION}",
  "a2aAgentDefinition": {
    "jsonAgentCard": ${AGENT_CARD_JSON}
  },
  "importedAgent": {
    "agent": "${AR_AGENT_NAME}"
  }
}
EOF
```

```sh
# get (list) all "imported from agent registry" agents registered with discovery engine (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq '.agents[]? | select(.importedAgent != null) | {displayName: .displayName, importedAgent: .importedAgent.agent, name: .name}'
```

## gateway

```sh
# bind discovery engine instance (ge app) to agent gateway
curl -X PATCH "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}?updateMask=agentGatewaySetting.defaultEgressAgentGateway.name" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "agentGatewaySetting": {
    "defaultEgressAgentGateway": {
      "name": "projects/${PROJ_NO}/locations/${REGION}/agentGateways/${AGW_NAME}"
    }
  }
}
EOF
```

```sh
# show config for discovery engine instance (ge app)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJ_ID}" | jq .
```

```sh
# show agent gateway config on discovery engine instance (ge app)
curl -s -X GET "https://global-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq '{name: .name, displayName: .displayName, agentGatewaySetting: .agentGatewaySetting}'
```

## testing

```sh
# set vars
export SLUG="foo"
export GE_LOCATION="global"
export GE_APP_NAME="app-${SLUG}-${GE_LOCATION}"

echo ${SLUG}
echo ${GE_LOCATION}
echo ${GE_APP_NAME}
```

```sh
# fetch vars
export PROJ_ID=$(gcloud config list --format="value(core.project)")
export PROJ_NO=$(gcloud projects describe $PROJ_ID --format="value(projectNumber)")
export ORG_ID=$(gcloud projects get-ancestors ${PROJ_ID} --format="value(id)" | tail -n 1)

echo ${PROJ_ID}
echo ${PROJ_NO}
echo ${ORG_ID}
```

```sh
# fetch discovery engine instance (ge app) id
export GE_APP_ID=$(curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq -r --arg name "${GE_APP_NAME}" '.engines[] | select(.displayName==$name) | .name | split("/") | last')
echo ${GE_APP_ID}
```

```sh
# extract registered discovery engine agent resource id
export GE_CUSTOM_AGENT_ID=$(curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  | jq -r --arg name "${RE_AGENT_NAME}" '.agents[] | select(.displayName==$name) | .name | split("/") | last')
echo ${GE_CUSTOM_AGENT_ID}
```

```sh
export QUERY="what is the capital of uzbekistan"
export QUERY="what is the capital of azerbaijan"
echo ${QUERY}
```

```sh
# query ge (default_assistant) w/ stream formatted output
curl --no-buffer -s -X POST "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/global/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant:streamAssist" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" \
  -H "Content-Type: application/json" \
  -d @- <<EOF | jq -j -r --unbuffered 'if type == "array" then .[] else . end | .answer.replies[]?.groundedContent?.content?.text // empty'
{
  "query": {
    "parts": [
      {
        "text": "${QUERY}"
      }
    ]
  }
}
EOF
```

## logging

### user

```sh
# show ge user activity logs
gcloud logging read \
  'log_id("discoveryengine.googleapis.com/gemini_enterprise_user_activity") AND jsonPayload.request.query.parts.text:*' \
  --project=${PROJ_ID} \
  --limit=5 \
  --order=desc \
  --format='table(
    timestamp.date(format="%Y-%m-%d %H:%M:%S", tz=LOCAL):label=TIME,
    jsonPayload.request.query.parts[0].text.trailoff(60):label=USER_QUERY,
    jsonPayload.serviceTextReply.yesno(no="").trailoff(60):label=GENERATED_REPLY
  )'
```

### data stores

```sh
# list all ge datastores (default collection)
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/dataStores" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" | jq '.dataStores[]? | {displayName: .displayName, name: .name}'
```

```sh
# list all ge datastores linked to a specific ge app
curl -s -X GET "https://${GE_LOCATION}-discoveryengine.googleapis.com/v1/projects/${PROJ_ID}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" | jq '.dataStores'
```
