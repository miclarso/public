# agent platform

## enable required apis

> Enable APIs to access full platform capabilities...

```sh
# enable apis (agent platform bundle, part 1)
gcloud services enable \
  agentregistry.googleapis.com \
  agentidentity.googleapis.com \
  aiplatform.googleapis.com \
  apphub.googleapis.com \
  apptopology.googleapis.com \
  cloudapiregistry.googleapis.com \
  cloudtrace.googleapis.com \
  compute.googleapis.com \
  dataform.googleapis.com \
  iam.googleapis.com \
  iamconnectors.googleapis.com \
  iap.googleapis.com \
  logging.googleapis.com \
  modelarmor.googleapis.com \
  monitoring.googleapis.com \
  networksecurity.googleapis.com \
  networkservices.googleapis.com \
  notebooks.googleapis.com
```

```sh
# enable apis (agent platform bundle, part 2)
gcloud services enable \
  observability.googleapis.com \
  securitycenter.googleapis.com \
  saasservicemgmt.googleapis.com \
  storage.googleapis.com \
  telemetry.googleapis.com \
  texttospeech.googleapis.com
```

```sh
# enable apis (gemini enterprise)
gcloud services enable \
  discoveryengine.googleapis.com
```

```sh
# enable apis (more services)
gcloud services enable \
  dlp.googleapis.com
```

## changelog

<tbd>
- Service Extensions API
- `serviceextensions.googleapis.com`
- tbd

2026-06-18
- Agent Identity API
- `agentidentity.googleapis.com`
- https://docs.cloud.google.com/iam/docs/release-notes#June_18_2026

2026-06-15
- Security Command Center API
- `securitycenter.googleapis.com`
- https://docs.cloud.google.com/security-command-center/docs/reference/rest

2026-05-30
- App Lifecycle Manager API
- `saasservicemgmt.googleapis.com`
- https://docs.cloud.google.com/saas-runtime/docs/reference/rest

## gateway min set

for agent gateway "standalone" 

> [!note]
> doesn't include runtime dependencies (ie, not super useful)

```sh
gcloud services enable \
  compute.googleapis.com \
  networksecurity.googleapis.com \
  networkservices.googleapis.com \
  dns.googleapis.com \
  iam.googleapis.com \
  agentregistry.googleapis.com \
  modelarmor.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

## agent runtime baseline

allow for agent runtime endpoint access

- https://agentregistry.googleapis.com (tool and service discovery)
- https://aiplatform.mtls.googleapis.com (agent runtime & gemini llm calls)
- https://${REGION}-aiplatform.mtls.googleapis.com (regional Vertex AI mTLS)
- https://${REGION}-aiplatform.googleapis.com (regional Vertex AI standard endpoint)
- https://aiplatform.${REGION}.rep.googleapis.com (regional endpoint)
- https://cloudresourcemanager.mtls.googleapis.com (project number and resource resolution)
- https://iamcredentials.mtls.googleapis.com (credential and token generation)
- https://telemetry.mtls.googleapis.com (metrics and trace export)

```sh
# create endpoint service (with multiple entries)
gcloud agent-registry services create gapi-core-services \
  --location=${REGION} \
  --display-name="gapi.core.services" \
  --description="core google apis and services" \
  --endpoint-spec-type=no-spec \
  --interfaces=protocolBinding=JSONRPC,url=https://agentregistry.googleapis.com \
  --interfaces=protocolBinding=JSONRPC,url=https://aiplatform.mtls.googleapis.com \
  --interfaces=protocolBinding=JSONRPC,url=https://${REGION}-aiplatform.mtls.googleapis.com \
  --interfaces=protocolBinding=JSONRPC,url=https://${REGION}-aiplatform.googleapis.com \
  --interfaces=protocolBinding=JSONRPC,url=https://aiplatform.${REGION}.rep.googleapis.com \
  --interfaces=protocolBinding=JSONRPC,url=https://cloudresourcemanager.mtls.googleapis.com \
  --interfaces=protocolBinding=JSONRPC,url=https://iamcredentials.mtls.googleapis.com \
  --interfaces=protocolBinding=JSONRPC,url=https://telemetry.mtls.googleapis.com
```

```sh
# list registry regional endpoints
gcloud agent-registry endpoints list --location=${REGION} \
  --flatten="interfaces[]" \
  --format="table(displayName, name.basename():label=ENDPOINT_ID, interfaces.url:label=URL)"
```
