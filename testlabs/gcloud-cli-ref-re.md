# gcloud cli reference

for agent runtime (fka agent engine, aka reasoning engine)

## reasoning engine

Supported locations
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/agent-locations
- us-central1
- us-east1
- us-west1
- europe-west4
- europe-west1
- europe-north1

```sh
# set vars
export RE_AGENT_NAME="agent-dj"
export REGION="us-east1"
echo ${RE_AGENT_NAME}
echo ${REGION}
```

## engine id

```sh
# fetch re engine id
export RE_ENGINE_ID=$(curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  | jq -r --arg name "${RE_AGENT_NAME}" '.reasoningEngines[] | select(.displayName==$name) | .name | split("/") | last')
echo ${RE_ENGINE_ID}
```

## agent identity

```sh
# fetch agent runtime (reasoning engine) agent identity
export RE_AGENT_IDENTITY=$(curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "Content-Type: application/json" \
  | jq -r '"principal://" + .spec.effectiveIdentity')
echo ${RE_AGENT_IDENTITY}
```

```sh
# verify re agent identity and gateway config
curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  | jq '{displayName: .displayName, name: .name, effectiveIdentity: .spec.effectiveIdentity, agentGatewayConfig: .spec.deploymentSpec.agentGatewayConfig}'
```

```sh
# fetch re agent identity (via rest)
export RE_AGENT_IDENTITY=$(curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  | jq -r '.spec.effectiveIdentity')
echo ${RE_AGENT_IDENTITY}
```

```sh
# fetch re agent identity (via agent registry)
export RE_AGENT_IDENTITY=$(gcloud alpha agent-registry agents list \
  --project=${PROJ_ID} --location=${REGION} --filter="displayName=${RE_AGENT_NAME}" \
  --format="value(attributes.'agentregistry.googleapis.com/system/RuntimeIdentity'.principal)")
echo ${RE_AGENT_IDENTITY}
```

> [!warning]
> deleting stuff!

```sh
# delete reasoning engine
curl -X DELETE "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json"
```

```sh
# set var
export OPERATION_ID="5636446592274792448"
echo ${OPERATION_ID}
```

```sh
# check op status
curl -X GET "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJ_ID}/locations/${REGION}/operations/${OPERATION_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json"
```

## env vars

```sh
# show re engine env vars
curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  | jq -r '.spec.deploymentSpec.env[] | "\(.name)=\(.value)"'
```

## query

> agent-qotd

```sh
# stream query reasoning engine (streamQuery)
curl --no-buffer -s -X POST "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJ_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}:streamQuery" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJ_ID}" \
  -d @- <<EOF | jq -r --unbuffered 'if type == "array" then .[] else . end | select(.content.parts != null) | .content.parts[].text // empty'
{
  "input": {
    "message": "what is the quote of the day?",
    "user_id": "test-user"
  }
}
EOF
