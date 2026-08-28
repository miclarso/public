
# gcloud cli reference

for agent gateway

## aiplatform

```sh
# show aiplatform requests
gcloud logging read \
  'resource.type="networkservices.googleapis.com/Gateway" AND httpRequest.requestUrl:"aiplatform"' \
  --project=${PROJ_ID} \
  --limit=15 \
  --format='table(
    timestamp.date(tz=LOCAL):label=TIMESTAMP,
    httpRequest.requestMethod:label=METHOD,
    httpRequest.status:label=STATUS,
    httpRequest.requestUrl.basename():label=ENDPOINT_LEAF,
    httpRequest.requestUrl.trailoff(120):label=URL
  )'
```

## agent gateway

```sh
# set vars
export SLUG="foo"
export REGION="us-east1"
export AGW_NAME="agw-${SLUG}-${REGION}-ata"
echo ${SLUG}
echo ${REGION}
echo ${AGW_NAME}
```

```sh
# list agent gateways
gcloud alpha network-services agent-gateways list --location=${REGION}
```

```sh
# describe agent gateway
gcloud alpha network-services agent-gateways describe ${AGW_NAME} --location=${REGION}
```

> [!warning]
> deleting stuff!
> 1. unbind all reasoning engines from gateway
> 2. delete authz policy (delegation)
> 3. delete authz [service] extension
> 4. delete gateway

### authz

```sh
# check then delete authz policy (delegation) binding
gcloud beta network-security authz-policies list --location=${REGION}

gcloud beta network-security authz-policies delete ${AGW_NAME}-authz-policy-profile-iap --location=${REGION}
```

```sh
# check then delete authz [service] extension
gcloud beta service-extensions authz-extensions list --location=${REGION}

gcloud beta service-extensions authz-extensions delete ${AGW_NAME}-svc-ext-authz-iap-enforced --location=${REGION}
```

```sh
# check then delete gateway
gcloud alpha network-services agent-gateways list --location=${REGION}

gcloud alpha network-services agent-gateways delete ${AGW_NAME} --location=${REGION}
```

```sh
# fetch psc na uri
export PSC_NA_URI=$(gcloud compute network-attachments describe psc-na-${REGION}-agw \
  --region=${REGION} \
  --format="value(selfLink.scope(v1))")
echo ${PSC_NA_URI}
```

### logging

```sh
# show gateway logs (policy info, exclude connect method)
gcloud logging read \
  'resource.type="networkservices.googleapis.com/Gateway" AND NOT httpRequest.requestMethod="CONNECT"' \
  --project=${PROJ_ID} \
  --limit=10 \
  --format='table(
    timestamp.date(format="%Y-%m-%d %H:%M:%S", tz=LOCAL):label=TIMESTAMP,
    httpRequest.remoteIp,
    httpRequest.serverIp,
    jsonPayload.enforcedGatewaySecurityPolicy.serverNameIndication,
    jsonPayload.enforcedGatewaySecurityPolicy.matchedRules.action,
    jsonPayload.enforcedGatewaySecurityPolicy.matchedRules.name
  )'
```

```sh
# show gateway logs (policy info for mcp calls)
gcloud logging read \
  'resource.type="networkservices.googleapis.com/Gateway" AND jsonPayload.agentGatewayInfo.mcpInfo:*' \
  --project=${PROJ_ID} \
  --limit=10 \
  --format='table(
    timestamp.date(format="%Y-%m-%d %H:%M:%S", tz=LOCAL):label=TIMESTAMP,
    httpRequest.remoteIp,
    httpRequest.serverIp,
    jsonPayload.enforcedGatewaySecurityPolicy.serverNameIndication,
    jsonPayload.enforcedGatewaySecurityPolicy.matchedRules.action,
    jsonPayload.enforcedGatewaySecurityPolicy.matchedRules.name
  )'
```

```sh
# show agent gateway access logs
gcloud logging read \
  'resource.type="networkservices.googleapis.com/Gateway" AND httpRequest.requestUrl:*' \
  --project=${PROJ_ID} \
  --limit=10 \
  --order=desc \
  --format='table(
    timestamp.date(format="%Y-%m-%d %H:%M:%S", tz=LOCAL):label=TIMESTAMP,
    httpRequest.requestMethod:label=METHOD,
    httpRequest.status:label=STATUS,
    jsonPayload.authzPolicyInfo.result:label=AUTHZ,
    httpRequest.serverIp:label=DEST_IP,
    httpRequest.requestUrl.trailoff(100):label=URL
  )'
```

```sh
# show agent gateway access logs (with client ip)
gcloud logging read \
  'resource.type="networkservices.googleapis.com/Gateway" AND httpRequest.requestUrl:*' \
  --project=${PROJ_ID} \
  --limit=10 \
  --order=desc \
  --format='table(
    timestamp.date(format="%Y-%m-%d %H:%M:%S", tz=LOCAL):label=TIMESTAMP,
    httpRequest.requestMethod:label=METHOD,
    httpRequest.status:label=STATUS,
    jsonPayload.authzPolicyInfo.result:label=AUTHZ,
    httpRequest.remoteIp:label=CLIENT_IP,
    httpRequest.serverIp:label=DEST_IP,
    httpRequest.requestUrl.trailoff(100):label=URL
  )'
```

## agent registry

an agent registry **`service`** is the underlying unified management resource (`gcloud agent-registry services`)

when creating a service, agent registry projects it into one of three _views_ based on the spec type...

* `--endpoint-spec-type=no-spec` $\rightarrow$ projects into **`endpoints`** (`gcloud agent-registry endpoints list`)
* `--mcp-server-spec-type=tool-spec` $\rightarrow$ projects into **`mcpServers`** (`gcloud agent-registry mcp-servers list`)
* `--agent-spec-content=...` $\rightarrow$ projects into **`agents`** (`gcloud agent-registry agents list`)

### agents

```sh
# fetch re agent registry id
export RE_AGENT_REGISTRY_ID=$(gcloud agent-registry agents list \
  --project=${AGW_PROJ_ID} --location=${REGION} --filter="displayName=${RE_AGENT_NAME}" \
  --format="value(name.basename())")
echo ${RE_AGENT_REGISTRY_ID}
```

```sh
# list registry agents (global)
gcloud alpha agent-registry agents list \
  --project=${PROJ_ID} \
  --location=global \
  --format="table(displayName, location, name.basename():label=AGENT_ID, protocols[0].interfaces[0].url.yesno(no='').trailoff(88):label=URL)"
```

```sh
# get (list) registry agents (global)
curl -s -X GET "https://agentregistry.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/global/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  | jq '.agents[]? | {displayName, url: .protocols[0].interfaces[0].url}'
```


```sh
# list registry agents (regional)
gcloud alpha agent-registry agents list \
  --project=${PROJ_ID} \
  --location=${REGION} \
  --format="table(displayName, location, name.basename():label=AGENT_ID, protocols[0].interfaces[0].url.yesno(no='').trailoff(88):label=URL)"
```

```sh
# get (list) registry agents (regional)
curl -s -X GET "https://agentregistry.googleapis.com/v1alpha/projects/${PROJ_ID}/locations/${REGION}/agents" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  | jq '.agents[]? | {displayName, url: .protocols[0].interfaces[0].url}'
```

### mcpServers

```sh
# register mcp server
gcloud agent-registry services create ${MCP_SERVER_RESOURCE_NAME} \
  --location=${REGION} \
  --display-name="${MCP_SERVER_DISPLAY_NAME}" \
  --description="mcp server for ${MCP_SERVER_RESOURCE_NAME}" \
  --mcp-server-spec-type=tool-spec \
  --mcp-server-spec-content=<localdir>/toolspec.json \
  --interfaces=url=${MCP_SERVER_URL},protocolBinding=JSONRPC
```

```sh
# list registry mcp servers (global)
gcloud alpha agent-registry mcp-servers list \
  --project=${PROJ_ID} \
  --location=global \
  --format="table(displayName, name.basename():label=MCP_SERVER_ID, interfaces[0].url:label=URL)"
```

```sh
# list registry mcp servers (global) w/ location path
gcloud agent-registry mcp-servers list \
  --project=${PROJ_ID} \
  --location=global \
  --format="table(displayName, name.sub('/[^/]+$', '/'):label=RESOURCE_LOCATION, name.basename():label=MCP_SERVER_ID, interfaces[0].url:label=URL)"
```

```sh
# list registry mcp servers (regional)
gcloud alpha agent-registry mcp-servers list \
  --project=${PROJ_ID} \
  --location=${REGION} \
  --format="table(displayName, name.basename():label=MCP_SERVER_ID, interfaces[0].url:label=URL)"
```

### endpoints

```sh
# set var
export REG_RESOURCE_NAME="www-${SLUG}-qotd"
echo ${REG_RESOURCE_NAME}
```

```sh
# register endpoint (for HTTP/JSON, eg rest)
gcloud alpha agent-registry services create ${REG_RESOURCE_NAME} \
  --project=${PROJ_ID} \
  --location=${REGION} \
  --display-name="qotd.${SLUG}.lab" \
  --endpoint-spec-type=no-spec \
  --interfaces="url=${ENDPOINT_URL},protocolBinding=HTTP_JSON"
```

```sh
# register endpoint (for JSONRPC, eg gapis)
gcloud alpha agent-registry services create ${ENDPOINT_RESOURCE_NAME} \
  --project=${PROJ_ID} \
  --location=${REGION} \
  --display-name="something.googleapis.com" \
  --endpoint-spec-type=no-spec \
  --interfaces="url=${ENDPOINT_HOST_NAME},protocolBinding=JSONRPC"
```

```sh
# list registry endpoints (global)
gcloud alpha agent-registry endpoints list \
  --project=${PROJ_ID} \
  --location=global \
  --format="table(displayName, name.basename():label=ENDPOINT_ID, interfaces[0].url:label=URL)"
```

```sh
# list registry endpoints (regional)
gcloud alpha agent-registry endpoints list \
  --project=${PROJ_ID} \
  --location=${REGION} \
  --format="table(displayName, name.basename():label=ENDPOINT_ID, interfaces[0].url:label=URL)"
```

```sh
# list registry endpoints (regional) w/ location path
gcloud agent-registry endpoints list \
  --project=${AGW_PROJ_ID} \
  --location=${REGION} \
  --format="table( \
    displayName, \
    name.sub('/[^/]+$', '/'):label=RESOURCE_LOCATION, \
    name.basename():label=ENDPOINT_ID, \
    interfaces[].url.list(separator='
'):label=URLS \
  )"
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
# set var
export REG_RESOURCE_ID=agentregistry-00000000-0000-0000-89db-9d8892c95941
echo ${REG_RESOURCE_ID}
```

```sh
# list registry endpoint details by name
gcloud alpha agent-registry endpoints list \
  --filter="name=${REG_RESOURCE_ID}" \
  --location=${REGION} \
  --project=${PROJ_ID} \
  --format="table(displayName, name.basename():label=ENDPOINT_ID, interfaces[0].url:label=URL)"
```

**NOTE** ^-- this does not work in alpha

```sh
# list registry endpoint details by name (alt jq)
gcloud alpha agent-registry endpoints list \
  --location=${REGION} \
  --project=${PROJ_ID} \
  --format=json | jq --arg reg_name "${REG_RESOURCE_ID}" '.[] | select(.name | endswith($reg_name)) | {displayName: .displayName, endpointId: (.name | split("/") | last), url: .interfaces[0].url}'
```

```sh
# set var
export DISPLAY_NAME=qotd.bar.lab
echo ${DISPLAY_NAME}
```

```sh
# list registry endpoint details by display name
gcloud alpha agent-registry endpoints list \
  --filter="displayName=${DISPLAY_NAME}" \
  --location=${REGION} \
  --project=${PROJ_ID} \
  --format="table(displayName, name.basename():label=ENDPOINT_ID, interfaces[0].url:label=URL)"
```

```sh
# describe registry service by resource name
gcloud alpha agent-registry services describe www-${SLUG}-qotd \
  --project=${PROJ_ID} \
  --location=${REGION}
```

### services

```sh
# list registry regional services
gcloud agent-registry services list --location=${REGION} \
  --format="table(displayName, name.basename():label=RESOURCE_NAME, interfaces[0].url:label=URL, registryResource.basename())"
```

```sh
# create multi endpoint service (no shell vars)
gcloud alpha agent-registry services create all-gapis-global \
    --location=${REGION} \
    --display-name="all global google apis consolidated" \
    --description="Google APIs for agent infrastructure" \
    --endpoint-spec-type=no-spec \
    --interfaces='[
        {"protocolBinding": "JSONRPC", "url": "https://cloudresourcemanager.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://cloudresourcemanager.mtls.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://aiplatform.googleapis.com/"},
        {"protocolBinding": "JSONRPC", "url": "https://logging.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://logging.mtls.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://monitoring.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://monitoring.mtls.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://oauth2.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://telemetry.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://telemetry.mtls.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://trace.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://trace.mtls.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://iap.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://iap.mtls.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://agentregistry.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://agentregistry.mtls.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://discoveryengine.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://discoveryengine.mtls.googleapis.com"}
    ]'
```

```sh
# create multi endpoint service (escaped quotes)
gcloud agent-registry services create fancy-service-123 \
    --location=${REGION} \
    --display-name="curated.and.consolidated.apis.com" \
    --description="the service of the future" \
    --endpoint-spec-type=no-spec \
    --interfaces="[
        {\"protocolBinding\": \"JSONRPC\", \"url\": \"https://telemetry.googleapis.com\"},
        {\"protocolBinding\": \"JSONRPC\", \"url\": \"https://${REGION}-aiplatform.googleapis.com\"},
        {\"protocolBinding\": \"JSONRPC\", \"url\": \"https://cloudresourcemanager.googleapis.com\"},
        {\"protocolBinding\": \"JSONRPC\", \"url\": \"https://iamcredentials.googleapis.com\"}
    ]"
```

```sh
# create multi endpoint service (shell quote concat)
gcloud agent-registry services create fancy-service-123 \
    --location=${REGION} \
    --display-name="curated.and.consolidated.apis.com" \
    --description="the service of the future" \
    --endpoint-spec-type=no-spec \
    --interfaces='[
        {"protocolBinding": "JSONRPC", "url": "https://telemetry.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://'"${REGION}"'-aiplatform.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://cloudresourcemanager.googleapis.com"},
        {"protocolBinding": "JSONRPC", "url": "https://iamcredentials.googleapis.com"}
    ]'
```

```sh
# create multi endpoint service (repeated flag)
gcloud agent-registry services create fancy-service-123 \
    --location=${REGION} \
    --display-name="curated.and.consolidated.apis.com" \
    --description="the service of the future" \
    --endpoint-spec-type=no-spec \
    --interfaces="url=https://telemetry.googleapis.com,protocolBinding=JSONRPC" \
    --interfaces="url=https://${REGION}-aiplatform.googleapis.com,protocolBinding=JSONRPC" \
    --interfaces="url=https://cloudresourcemanager.googleapis.com,protocolBinding=JSONRPC" \
    --interfaces="url=https://iamcredentials.googleapis.com,protocolBinding=JSONRPC"
```

```sh
# create list of interfaces (heredoc)
INTERFACES_JSON=$(cat <<EOF
[
  {"protocolBinding": "JSONRPC", "url": "https://telemetry.googleapis.com"},
  {"protocolBinding": "JSONRPC", "url": "https://${REGION}-aiplatform.googleapis.com"},
  {"protocolBinding": "JSONRPC", "url": "https://cloudresourcemanager.googleapis.com"},
  {"protocolBinding": "JSONRPC", "url": "https://iamcredentials.googleapis.com"}
]
EOF
)
```

```sh
# verify list
echo ${INTERFACES_JSON}
```

```sh
# create multi endpoint service (heredoc)
gcloud agent-registry services create fancy-service-123 \
    --location=${REGION} \
    --display-name="curated.and.consolidated.apis.com" \
    --description="the service of the future" \
    --endpoint-spec-type=no-spec \
    --interfaces="${INTERFACES_JSON}"
```

```sh
# list registry regional endpoints (verify registration)
gcloud agent-registry endpoints list --location=${REGION} \
  --flatten="interfaces[]" \
  --format="table(displayName, name.basename():label=ENDPOINT_ID, interfaces.url:label=URL)"
```

## authz extensions

> network security (service extensions) -> custom provider -> authz extensions

```sh
# list authz extensions
gcloud beta service-extensions authz-extensions list --location=${REGION}
```

```sh
# describe authz extension (dry run)
gcloud beta service-extensions authz-extensions describe ${AGW_NAME}-svc-ext-authz-iap-dryrun --location=${REGION}
```

```sh
# describe authz extension (enforced)
gcloud beta service-extensions authz-extensions describe ${AGW_NAME}-svc-ext-authz-iap-enforced --location=${REGION}
```

```sh
# patch config (dry run -> enforced)
curl -X PATCH "https://networksecurity.googleapis.com/v1alpha1/projects/${PROJ_ID}/locations/${REGION}/authzPolicies/${AGW_NAME}-authz-policy-profile-iap?updateMask=target,action,customProvider" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  -d @- <<EOF
{
  "name": "projects/${PROJ_ID}/locations/${REGION}/authzPolicies/${AGW_NAME}-authz-policy-profile-iap",
  "target": {
    "resources": [
      "projects/${PROJ_ID}/locations/${REGION}/agentGateways/${AGW_NAME}"
    ]
  },
  "action": "CUSTOM",
  "customProvider": {
    "authzExtension": {
      "resources": [
        "projects/${PROJ_ID}/locations/${REGION}/authzExtensions/${AGW_NAME}-svc-ext-authz-iap-enforced"
      ]
    }
  }
}
EOF
```

```sh
# patch config (enforced -> dry run)
curl -X PATCH "https://networksecurity.googleapis.com/v1alpha1/projects/${PROJ_ID}/locations/${REGION}/authzPolicies/${AGW_NAME}-authz-policy-profile-iap?updateMask=target,action,customProvider" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJ_ID}" \
  -d @- <<EOF
{
  "name": "projects/${PROJ_ID}/locations/${REGION}/authzPolicies/${AGW_NAME}-authz-policy-profile-iap",
  "target": {
    "resources": [
      "projects/${PROJ_ID}/locations/${REGION}/agentGateways/${AGW_NAME}"
    ]
  },
  "action": "CUSTOM",
  "customProvider": {
    "authzExtension": {
      "resources": [
        "projects/${PROJ_ID}/locations/${REGION}/authzExtensions/${AGW_NAME}-svc-ext-authz-iap-dryrun"
      ]
    }
  }
}
EOF
```

## authz policies

```sh
# set var
export REG_LOCATION="global"
echo ${REG_LOCATION}
```

```sh
# set vars
export TARGET_MCP_NAME="storage.googleapis.com"
export TARGET_MPC_LOCATION="global"
export SOURCE_AGENT_NAME="agent-datafetch"
export SOURCE_AGENT_LOCATION="${REGION}"
echo ${TARGET_MCP_NAME}
echo ${SOURCE_AGENT_NAME}
echo ${TARGET_MPC_LOCATION}
echo ${SOURCE_AGENT_LOCATION}
```

```sh
# fetch source agent identity
export SOURCE_AGENT_IDENTITY=$(gcloud alpha agent-registry agents list \
  --project=${PROJ_ID} \
  --location=${SOURCE_AGENT_LOCATION} \
  --filter="displayName=${SOURCE_AGENT_NAME}" \
  --format=json \
  | jq -r '.[0].attributes["agentregistry.googleapis.com/system/RuntimeIdentity"].principal')
echo ${SOURCE_AGENT_IDENTITY}
```

```sh
# fetch mcp server id (urn)
export TARGET_MCP_URN=$(gcloud alpha agent-registry mcp-servers list \
  --project=${PROJ_ID} \
  --location=${TARGET_MPC_LOCATION} \
  --filter="displayName=${TARGET_MCP_NAME}" \
  --format="value(mcpServerId)")
echo ${TARGET_MCP_URN}
```

### agentRegistry

```sh
# fetch etag
export IAP_ETAG=$(curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJ_NO}/locations/${REG_LOCATION}/iap_web/agentRegistry:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" -d '{}' | jq -r '.etag')
echo "Active Etag: ${IAP_ETAG}"
```

```sh
# create iam policy file (w/ etag)... allow agent set to registry
cat > cfg/policy.json <<EOF
{
  "policy": {
    "bindings": [
      {
        "role": "roles/iap.egressor",
        "members": [
          "${RE_AGENT_ID_SET}"
        ]
      }
    ],
    "etag": "${IAP_ETAG}"
  }
}
EOF
```

```sh
# create iam policy file (w/ etag)... allow agent to mcp server with conditions
cat > cfg/policy.json <<EOF
{
  "policy": {
    "bindings": [
      {
        "role": "roles/iap.egressor",
        "members": [
          "${RE_AGENT_IDENTITY}"
        ],
        "condition": {
          "title": "restrict ${AGENT_NAME} to read only ${MCP_NAME}",
          "expression": "api.getAttribute('iap.googleapis.com/mcpServer', '') == '${MCP_URN}' && api.getAttribute('iap.googleapis.com/mcp.tool.isReadOnly', false) == true"
        }
      }
    ],
    "etag": "${IAP_ETAG}",
    "version": 3
  }
}
EOF
```

```sh
# apply policy
curl -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJ_NO}/locations/${REG_LOCATION}/iap_web/agentRegistry:setIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" \
  -d @cfg/policy.json
```

```sh
# get iap policy for target >> @ registry ${location} : agentRegistry
curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJ_NO}/locations/${REG_LOCATION}/iap_web/agentRegistry:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" -d '{"options": {"requestedPolicyVersion": 3}}' | jq .
```

### agents

```sh
# eg,
export AGENT_NAME="agent-echo" # or
export AGENT_NAME="agent-qotd"
```

```sh
# fetch agent registry resource id
export REGISTRY_ID=$(gcloud agent-registry agents list \
  --location=${REGION} \
  --filter="displayName=${AGENT_NAME}" \
  --format="value(name.basename())")
echo ${REGISTRY_ID}
```

```sh
# show agent registry details (by registry id)
gcloud agent-registry agents describe ${REGISTRY_ID} --location=${REGION}
```

```sh
# show iap iam policy for agent
gcloud beta iap web get-iam-policy \
  --region=${REGION} \
  --resource-type=agent-registry \
  --agent=${REGISTRY_ID}
```

```sh
# post to get iap v3 iam policy binding on agent
curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJ_NO}/locations/${REGION}/iap_web/agentRegistry/agents/${REGISTRY_ID}:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJ_ID}" \
  -H "Content-Type: application/json" \
  -d '{"options": {"requestedPolicyVersion": 3}}' | jq .
```

### mcpServers

```sh
# eg,
export MCP_SERVER_NAME="mcp-math"
```

```sh
# show mcp server registry details
gcloud agent-registry services describe ${MCP_SERVER_NAME} --location=${REGION}
```

```sh
# fetch mcp server [registry] id
export MCP_SERVER_UID=$(gcloud agent-registry services describe ${MCP_SERVER_NAME} \
  --location=${REGION} \
  --format="value(registryResource.basename())")
echo ${MCP_SERVER_UID}
```

```sh
# show iap iam policy for mcp server
gcloud beta iap web get-iam-policy \
  --region=${REGION} \
  --resource-type=agent-registry \
  --mcp-server=${MCP_SERVER_UID}
```

```sh
# get iap policy for target >> @ registry ${location} : agentRegistry : mcp server : ${target-mcp-server}
curl -X POST "https://iap.googleapis.com/v1/projects/${PROJ_NO}/locations/${REGION}/iap_web/agentRegistry/mcpServers/${MCP_SERVER_UID}:getIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" -d '{}'
```

```sh
# get iap policy for target >> @ registry ${location} : agentRegistry : mcp server : ${target-mcp-server}
curl -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJ_NO}/locations/${TARGET_MPC_LOCATION}/iap_web/agentRegistry/mcpServers/${TARGET_REG_NAME}:getIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" -d '{}'
```

```sh
# list registry regional mcp servers
gcloud agent-registry mcp-servers list --location=${REGION} --format="table(displayName, interfaces.url)"
```

```sh
# show mcp server registry details
gcloud agent-registry services describe ${MCP_SERVER_RESOURCE_NAME} --location=${REGION}
```

```sh
# fetch mcp server registry id
export MCP_SERVER_REGISTRY_ID=$(gcloud agent-registry services describe ${MCP_SERVER_RESOURCE_NAME} \
  --location=${REGION} \
  --format="value(registryResource.basename())")
echo ${MCP_SERVER_REGISTRY_ID}
```

```sh
# fetch mcp server urn
export MCP_SERVER_URN=$(gcloud agent-registry mcp-servers describe ${MCP_SERVER_REGISTRY_ID} \
  --location=${REGION} \
  --format="value(mcpServerId)")
echo ${MCP_SERVER_URN}
```

### endpoints

```sh
# set var for endpoint display name
export ENDPOINT_DISPLAY_NAME="telemetry.googleapis.com"
echo ${ENDPOINT_DISPLAY_NAME}
```

```sh
# fetch endpoint registry id
export ENDPOINT_REGISTRY_ID=$(gcloud agent-registry services list \
  --location=${REGION} \
  --filter="displayName=${ENDPOINT_DISPLAY_NAME}" \
  --format="value(registryResource.basename())")
echo ${ENDPOINT_REGISTRY_ID}
```

```sh
# get iap policy for target >> @ registry ${location} : agentRegistry : endpoints : ${endpoint-registry-id}
curl -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJ_NO}/locations/${REGION}/iap_web/agentRegistry/endpoints/${ENDPOINT_REGISTRY_ID}:getIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" -d '{}'
```

### remove

```sh
# remove all access policies on target
curl -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJ_NO}/locations/${REG_LOCATION}/iap_web/agentRegistry/mcpServers/${MCP_REG_NAME}:setIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "X-Goog-User-Project: ${PROJ_ID}" -H "Content-Type: application/json" \
-d @- <<EOF
{
  "policy":
    {
      "etag": "${IAP_ETAG}",
      "bindings": []
    }
} 
EOF
```

### audit

```sh
# list unique target hostnames logged by agent gateway
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" \
  AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=200 \
  --format="value(httpRequest.requestUrl)" | awk -F/ '{print $1"//"$3}' | sort -u
```

```sh
# list unique full request urls logged by agent gateway
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" \
  AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=200 \
  --format="value(httpRequest.requestUrl)" | sort -u
```

```sh
# list unique urls with http status and iap authorization result
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" \
  AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=200 \
  --format="value(httpRequest.status, jsonPayload.authzPolicyInfo.result, httpRequest.requestUrl)" | sort -u
```

```sh
# list all registered endpoints and mcp servers granting iap egress to RE_AGENT_IDENTITY
gcloud agent-registry services list --location=${REGION} \
  --format="value(displayName, registryResource.basename())" | while read -r name id; do
  
  POLICY=$(gcloud beta iap web get-iam-policy --resource-type=agent-registry \
    --region=${REGION} --endpoint="$id" --format=json 2>/dev/null || \
  gcloud beta iap web get-iam-policy --resource-type=agent-registry \
    --region=${REGION} --mcp-server="$id" --format=json 2>/dev/null)
    
  if echo "$POLICY" | grep -q "${RE_AGENT_IDENTITY}"; then
    echo "=== Allowed Egress Target: $name ($id) ==="
    echo "$POLICY"
  fi
done
```

> finding all the unique urls before going into enforced mode...

> option 1 - list

```sh
# list unique urls with http status and iap authorization result
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" \
  AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=200 \
  --format="value(httpRequest.status, jsonPayload.authzPolicyInfo.result, httpRequest.requestUrl)" | sort -u
```

```sh
# list unique hostnames with http status and iap authorization result
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" \
  AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=200 \
  --format="value(httpRequest.status, jsonPayload.authzPolicyInfo.result, httpRequest.requestUrl)" \
  | sed -E 's|(https?://[^/:]+).*|\1|' \
  | sort -u
```

```sh
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" \
  AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=200 \
  --format="value(httpRequest.requestUrl)" \
  | sed -E 's|(https?://[^/:]+).*|\1|' \
  | sort -u
```

> option 2 - table

```sh
# table
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" \
  AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=200 \
  --format="value(httpRequest.status, jsonPayload.authzPolicyInfo.result, httpRequest.requestUrl)" \
  | sort -u \
  | awk 'BEGIN {print "STATUS\tIAP_AUTHZ\tURL"} {print $1"\t"$2"\t"$3}' | column -t
```

> option 3 - table + timestamp

```sh
# table + timestamp
gcloud logging read \
  "resource.type=\"networkservices.googleapis.com/Gateway\" \
  AND httpRequest.requestUrl:*" \
  --project=${PROJ_ID} \
  --limit=200 \
  --format="value(timestamp.date(format='%Y-%m-%d %H:%M:%S', tz=LOCAL), httpRequest.status, jsonPayload.authzPolicyInfo.result, httpRequest.requestUrl)" \
  | sort -k4,4 -u \
  | awk 'BEGIN {print "TIME\t\tSTATUS\tIAP_AUTHZ\tURL"} {print $1" "$2"\t"$3"\t"$4"\t"$5}' | column -t -s $'\t'
```

### logging

```sh
# show agw iap egress logs (unregistered deny)
gcloud logging read \
  "protoPayload.authorizationInfo.permission=\"iap.webServiceVersions.egressViaIAP\"" \
  --project=${PROJ_ID} \
  --limit=10 \
  --format='table(
    timestamp.date(tz=LOCAL):label=TIMESTAMP,
    protoPayload.resourceName:label=RESOURCE_NAME,
    protoPayload.status.message:label=STATUS,
    protoPayload.request.httpRequest.url:label=URL
  )'
```

```sh
# show traffic denied by authz policy
gcloud logging read \
  'resource.type="networkservices.googleapis.com/Gateway" AND (jsonPayload.authzPolicyInfo.result="DENIED" OR httpRequest.status=403)' \
  --project=${PROJ_ID} \
  --limit=10 \
  --format='table(
    timestamp.date(tz=LOCAL):label=TIMESTAMP,
    httpRequest.requestMethod:label=METHOD,
    httpRequest.status:label=STATUS,
    jsonPayload.enforcedGatewaySecurityPolicy.serverNameIndication:label=SNI,
    jsonPayload.authzPolicyInfo.result:label=AUTHZ_RESULT,
    jsonPayload.authzPolicyInfo.policies[0].name.basename():label=DENYING_POLICY
  )'
```

## iam principals

agent identities
- principalSet://agents.global.org-${ORG_ID}.system.id.goog/attribute.container/projects/${PROJ_NO}
- principalSet://agents.global.org-${ORG_ID}.system.id.goog/attribute.platformContainer/aiplatform/projects/${PROJ_NO}
- principal://agents.global.org-${ORG_ID}.system.id.goog/resources/aiplatform/projects/${PROJ_NO}/locations/${GE_LOCATION}/reasoningEngines/${RE_ENGINE_ID}
- principal://agents.global.org-${ORG_ID}.system.id.goog/resources/discoveryengine/projects/${PROJ_NO}/locations/global/collections/default_collection/engines/${GE_ENGINE_ID}
- principal://agents.global.org-${ORG_ID}.system.id.goog/resources/discoveryengine/projects/${PROJ_NO}/locations/global/engines/${GE_APP_ID}/assistants/default_assistant/agents/default/core_assistant
- principal://agents.global.org-${ORG_ID}.system.id.goog/resources/discoveryengine/projects/${PROJ_NO}/locations/global/engines/${GE_APP_ID}/assistants/default_assistant/agents/default/deep_research
- principal://agents.global.org-${ORG_ID}.system.id.goog/resources/discoveryengine/projects/${PROJ_NO}/locations/global/engines/${GE_APP_ID}/assistants/default_assistant/agents/default/idea_generation
- principal://agents.global.org-${ORG_ID}.system.id.goog/resources/discoveryengine/projects/${PROJ_NO}/locations/global/engines/${GE_APP_ID}/assistants/default_assistant/agents/user/{$AGENT_BUILDER_ID}

service accounts
- ${PROJ_NO}@gcp-sa-dep.iam.gserviceaccount.com
- service-${PROJ_NO}@gcp-sa-agentgateway.iam.gserviceaccount.com

```sh
# show principal (x) roles on project (y)
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${PRINCIPAL_ID}" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=IDENTITY)"
```

## psc

```sh
# fetch psc sa uri
export PSC_SA_URI=$(gcloud sql instances describe ${CSQL_NAME} --format="value(pscServiceAttachmentLink)")
echo ${PSC_SA_URI}
```

```sh
# fetch psc sa uri
export PSC_NA_URI=$(gcloud compute network-attachments describe psc-na-${SLUG}-${REGION} \
  --region=${REGION} \
  --format="value(selfLink)" | sed 's|https://www.googleapis.com/compute/v1/||')
echo ${PSC_NA_URI}
```

## cloud run

```sh
# query cloud run logs for 401 authorization errors
gcloud logging read \
  "resource.type=\"cloud_run_revision\" \
  AND resource.labels.service_name=\"${MCP_NAME}\" \
  AND (httpRequest.status=401 OR textPayload:\"401\")" \
  --project=${PROJ_ID} \
  --limit=10 \
  --format="table(
    timestamp.date(tz=LOCAL):label=TIMESTAMP,
    resource.labels.service_name:label=SERVICE,
    httpRequest.requestMethod:label=METHOD,
    httpRequest.status:label=STATUS,
    textPayload.trailoff(123):label=DETAILS
  )"
```

## model armor

```sh
# test model armor w/ dlp
curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" \
  "https://modelarmor.${REGION}.rep.googleapis.com/v1/projects/${PROJ_ID}/locations/${REGION}/templates/agw-foo-${REGION}-cta-modar-resp-template:sanitizeModelResponse" \
  -d '{
    "modelResponseData": {
      "text": "Bob Johnson SSN is 764-02-0001"
    }
  }' | jq .
```
