---
lab: agw-codelab
ver: public connectivity
rev: 01
---

# agent gateway

## (1) about

_Governing agentic workloads with Agent Gateway on Gemini Enterprise Agent Platform_
- https://codelabs.developers.google.com/cloudnet-agent-gateway#0

## (2) setup

```sh
# enable apis
gcloud services enable \
  compute.googleapis.com \
  serviceusage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  storage.googleapis.com \
  dns.googleapis.com
```

```sh
# check tf, uv, skaffold, envsubst installs
command -v terraform && terraform --version
command -v uv && uv --version
command -v skaffold && skaffold version
command -v envsubst && envsubst --version
```

```sh
# tf install (local bin)

# create local user bin and tmp
mkdir -p ~/bin ~/tmp

# download terraform
export TERRAFORM_VERSION=1.14.9
curl -o ~/tmp/terraform.zip https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# extract binary directly into ~/bin
unzip ~/tmp/terraform.zip -d ~/bin

# clean up archive
rm ~/tmp/terraform.zip

# add ~/bin to path in ~/.bashrc if not already present
grep -q 'export PATH="$HOME/bin:$PATH"' ~/.bashrc || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc

# reload bashrc
source ~/.bashrc
```

```sh
# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# install skaffold (if allowed on system: gcloud components install skaffold)
sudo apt-get install google-cloud-cli-skaffold

# install envsubst (gettext)
sudo apt-get install -y gettext-base
```

```sh
# check installs
command -v terraform && terraform --version
command -v uv && uv --version
command -v skaffold && skaffold version
command -v envsubst && envsubst --version
```

```sh
# set vars
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')
export ORG_ID=$(gcloud projects get-ancestors ${PROJECT_ID} | awk '$2 == "organization" {print $1}')
export REGION="us-central1"
export USER_EMAIL=$(gcloud auth list --filter="status:ACTIVE" --format="value(account)")

# Only required if using the secure private networking path
export DOMAIN_NAME="agw.example.com" 

echo ${PROJECT_ID}
echo ${PROJECT_NUMBER}
echo ${ORG_ID}
echo ${REGION}
echo ${USER_EMAIL}
echo ${DOMAIN_NAME}
```

## (3) repo

```sh
# start at project root dir
export PROJ_ROOT_DIR=$(pwd)
echo ${PROJ_ROOT_DIR}
```

```sh
# shallow clone repo to temp folder
git clone --depth=1 https://github.com/GoogleCloudPlatform/cloud-networking-solutions.git ./temp_agw
```

```sh
# copy agent-gateway demo folder to current directory
cp -r temp_agw/demos/agent-gateway ./

# delete temp repo
rm -rf temp_agw
```

```sh
# change dir
cd agent-gateway

# print tree
tree
```

```
.
├── cloudrun
│   ├── corporate-email.yaml.tmpl          # Cloud Run manifest template
│   ├── income-verification-api.yaml.tmpl  # Cloud Run manifest template
│   └── legacy-dms.yaml.tmpl               # Cloud Run manifest template
├── scripts
│   └── grant_agent_mcp_egress.sh          # Crucial helper for per-MCP IAP IAM bindings
├── skaffold.yaml.tmpl                     # Build & deploy pipeline for MCP servers
├── src
│   ├── corporate-email/                   # Proprietary MCP tool: Corporate Email
│   ├── income-verification-api/           # Proprietary MCP tool: Income Verification
│   ├── legacy-dms/                        # Proprietary MCP tool: Document Management
│   └── mortgage-agent                     # ADK Agent Application
│       ├── agent/agent.py                 # Core agent logic and prompt definitions
│       └── deploy_agent.py                # Script to deploy agent to Agent Runtime
└── terraform
    ├── example.tfvars                     # Core variables (networking flags, IAP modes)
    ├── main.tf                            # Root Terraform configuration
    └── modules                            # Infrastructure building blocks
        ├── agent-engine/                  # Agent Runtime provisioning
        ├── agent-gateway/                 # Agent Gateway & Service Extensions (IAP, Model Armor)
        ├── agent-registry-endpoints/      # Registering Google APIs & MCP servers
        ├── foundation/                    # Project bootstrap (APIs, SAs, Quotas)
        ├── mcp-cloud-run/                 # Cloud Run services & Artifact Registry
        ├── model-armor/                   # Model Armor templates & DLP configs
        ├── networking/                    # VPC, Subnets, PSC attachments, Cloud NAT
        └── observability/                 # Authorization Debugging Dashboard
```

## (4) tf config

```sh
# create gcs bucket for tf state
gcloud storage buckets create gs://${PROJECT_ID}-tfstate \
  --location=${REGION} \
  --uniform-bucket-level-access
```

```sh
# copy example backend template for edit
cp terraform/example.backend.conf terraform/backend.conf
```

```sh
# add values to tf backend config
cat > terraform/backend.conf <<EOF
bucket = "${PROJECT_ID}-tfstate"
prefix = "agent-gateway"
EOF
```

## (5) public dns

> [!note]
> #privatenetworking ... skipping here ... see [`agw-codelab-priv.md`](agw-codelab-priv.md)

## (6) tf vars

```sh
# copy example tfvars for edit
cp terraform/example.tfvars terraform/terraform.tfvars
```

```sh
# inject project id
sed -i "s/project_id = \"my-gcp-project-id\"/project_id = \"${PROJECT_ID}\"/" terraform/terraform.tfvars

# inject org id
sed -i "s/organization_id = \"123456789012\"/organization_id = \"${ORG_ID}\"/" terraform/terraform.tfvars

# inject user email to admin members
sed -i "s/platform_admin_members = \[\"user:admin@example.com\"\]/platform_admin_members = \[\"user:${USER_EMAIL}\"\]/" terraform/terraform.tfvars
```

```sh
# verify config values
grep -E "^(project_id|organization_id|platform_admin_members|agent_gateway_iap_iam_enforcement_mode)" terraform/terraform.tfvars
```

## (7) tf deploy

```sh
# tf init
cd terraform
terraform init -backend-config=backend.conf
```

```sh
# tf plan
terraform plan -out=tfplan
```

```sh
# tf apply
terraform apply tfplan
```

```log
module.agent_gateway[0].google_network_security_authz_policy.iap: Creation complete after 2m34s [id=projects/${PROJECT_ID}/locations/us-central1/authzPolicies/agent-gateway-iap-policy]
╷
│ Error: Error waiting to create AuthzPolicy: Error waiting for Creating AuthzPolicy: Error code 6, message: Failed to update tenant configuration for AgentGateway: generic::already_exists: Resource 'projects/${PROJECT_NO}/locations/us-central1/agentGatewayTenantAuthzConfigs/${CONFIG_ID}' already exists
│ 
│   with module.agent_gateway[0].google_network_security_authz_policy.model_armor[0],
│   on modules/agent-gateway/main.tf line 237, in resource "google_network_security_authz_policy" "model_armor":
│  237: resource "google_network_security_authz_policy" "model_armor" {
```

```sh
# tf apply (attempt 2)
terraform apply
```

## (8) show registry

> [!note]
> source `../terraform/modules/agent-registry-endpoints/scripts/register_endpoints.sh.tpl`

```sh
# list registry services (region)
gcloud alpha agent-registry services list \
  --project=${PROJECT_ID} --location=${REGION} \
  --format="table(displayName,interfaces.url)"

# list registry services (global)
gcloud alpha agent-registry services list \
  --project=${PROJECT_ID} --location=global \
  --format="table(displayName,interfaces.url)"
```

```sh
# list registry mcp servers
gcloud alpha agent-registry mcp-servers list \
  --project=${PROJECT_ID} --location=${REGION} \
  --format="table(displayName,interfaces.url)"
```

## (9) show gateway

```sh
# describe gateway
gcloud alpha network-services agent-gateways describe agent-gateway --location=${REGION}
```

## (10) show authz

```sh
# list authz extensions
gcloud beta service-extensions authz-extensions list --location=${REGION}
```

```sh
# describe authz extensions for iap
gcloud beta service-extensions authz-extensions describe agent-gateway-iap-authz --location=${REGION}

# describe authz extensions for model armor
gcloud beta service-extensions authz-extensions describe agent-gateway-ma-authz --location=${REGION}
```

```sh
# list authz policies
gcloud beta network-security authz-policies list --location=${REGION}

# describe authz policy for iap
gcloud beta network-security authz-policies describe agent-gateway-iap-policy --location=${REGION}

# describe authz policy for model armor
gcloud beta network-security authz-policies describe agent-gateway-ma-policy --location=${REGION}
```

## (11) deploy mcp

```sh
# set var (cloud run ingress setting)
export MCP_INGRESS="all"
echo ${MCP_INGRESS}
```

```sh
# change dir (project root dir)
cd ..
```

```sh
# substitute template values
envsubst '${PROJECT_ID} ${REGION} ${MCP_INGRESS}' < skaffold.yaml.tmpl > skaffold.yaml
for f in cloudrun/*.yaml.tmpl; do
  envsubst '${PROJECT_ID} ${REGION} ${MCP_INGRESS}' < "$f" > "${f%.tmpl}"
done
```

```sh
# grant iam service account user role (to self)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:${USER_EMAIL}" \
  --role="roles/iam.serviceAccountUser"
```

```sh
# deploy with skaffold
skaffold run
```

```sh
# verify run deployment
gcloud run services list --region=${REGION}
```

## (12) deploy agent

```sh
# change dir
cd src/mortgage-agent
```

```sh
# install dependencies
uv sync
```

```sh
# set var
export RE_AGENT_NAME="Mortgage Assistant Agent"
echo ${RE_AGENT_NAME}
```

```sh
# deploy agent to agent runtime
uv run python deploy_agent.py \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --enable-agent-identity \
  --agent-name="mortgage-agent" \
  --agent-gateway=projects/${PROJECT_ID}/locations/${REGION}/agentGateways/agent-gateway \
  --mcp-invoker-sa=$(terraform -chdir=../../terraform output -raw agent_mcp_invoker_email) \
  --model-endpoint-location=global
```

```sh
# fetch engine id (re is always regional)
export RE_ENGINE_ID=$(curl -s -X GET "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  | jq -r --arg name "Mortgage Assistant Agent" '.reasoningEngines[] | select(.displayName==$name) | .name | split("/") | last')
echo ${RE_ENGINE_ID}
```

```sh
# list registry agents
gcloud alpha agent-registry agents list \
  --project=${PROJECT_ID} --location=${REGION} \
  --format="table(displayName,protocols[0].interfaces[0].url)"
```

## (13) mcp policy

> [!note]
> agents discover mcp tools at runtime by listing `mcpServers` in the registry under projects/${PROJECT_ID}/locations/${REGION}

```sh
# change dir (back to ../agent-gateway)
cd ${PROJ_ROOT_DIR}/agent-gateway
```

> [!note]
> to apply `roles/iap.egressor` on every mcp server for member principal for ${RE_ENGINE_ID}... just fyi (do not run)
> ```sh
> # use case 0 - unconditional grant to all mcp servers for one agent
> ./scripts/grant_agent_mcp_egress.sh \
>  --mcp \
>  --agent-id ${RE_ENGINE_ID}
> ```

```sh
# use case 1 - unconditional grant to specific mcp servers
./scripts/grant_agent_mcp_egress.sh \
  --mcp \
  --agent-id ${RE_ENGINE_ID} \
  --mcp-filter "legacy-dms income-verification"
```

```sh
# use case 2 - conditional grant (subset of tools) to specific mcp servers
./scripts/grant_agent_mcp_egress.sh \
  --mcp \
  --agent-id ${RE_ENGINE_ID} \
  --mcp-filter "corporate-email" \
  --condition-expression "api.getAttribute('iap.googleapis.com/mcp.tool.isReadOnly', false) == true" \
  --condition-title "ReadOnlyToolsOnly" \
  --condition-description "Restrict ${RE_ENGINE_ID} to read-only tools on corporate-email"
```

> [!note]
> apply this to make write tools on `corporate-email` return `403 PermissionDenied` from iap `REQUEST_AUTHZ`... read-only tools continue to work

```sh
# fetch target mcp server registry uid
export TARGET_REG_UID=$(gcloud alpha agent-registry mcp-servers list \
  --project=${PROJECT_ID} \
  --location=${REGION} \
  --filter="displayName='corporate-email'" \
  --format="value(name.basename())")
echo ${TARGET_REG_UID}
```

```sh
# get iap policy for target >> @ registry ${location} : mcp server (iam v3)
curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/${REGION}/iap_web/agentRegistry/mcpServers/${TARGET_REG_UID}:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
  -d '{"options":{"requestedPolicyVersion":3}}' | jq .
```

## (14) test agent

> [!note]
> test in playground or run curls

```sh
# playground
echo "https://console.cloud.google.com/agent-platform/runtimes/locations/${REGION}/agent-engines/${RE_ENGINE_ID}/playground?project=${PROJECT_ID}"
```

> initial prompt

```sh
# call reasoning engine agent streamQuery
curl -s -X POST "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}:streamQuery" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @- <<EOF
{
  "input": {
    "message": "I am reviewing the Sterling familys current application. Can you summarize their 2024 and 2025 tax returns and verify if their total household income meets our 2026 debt-to-income requirements?",
    "user_id": "test-user"
  }
}
EOF
```

> follow-up prompt

```sh
# call reasoning engine agent streamQuery
curl -s -X POST "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}:streamQuery" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @- <<EOF
{
  "input": {
    "message": "Can you send a summary of this to my email jane@example.com",
    "user_id": "test-user"
  }
}
EOF
```

## (15) enforce iap

```sh
# update iap enforcement mode to null (enforcing)
sed -i 's/agent_gateway_iap_iam_enforcement_mode = "DRY_RUN"/agent_gateway_iap_iam_enforcement_mode = null/' terraform/terraform.tfvars
```

```sh
# verify config values
grep -E "^(project_id|organization_id|platform_admin_members|agent_gateway_iap_iam_enforcement_mode)" terraform/terraform.tfvars
```

```sh
# apply tf
terraform -chdir=terraform apply
```

> [!note]
> test in playground or run curls

```sh
# playground
echo "https://console.cloud.google.com/agent-platform/runtimes/locations/${REGION}/agent-engines/${RE_ENGINE_ID}/playground?project=${PROJECT_ID}"
```

```sh
# call reasoning engine agent streamQuery
curl -s -X POST "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}:streamQuery" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @- <<EOF
{
  "input": {
    "message": "I am reviewing the Sterling familys current application. Can you summarize their 2024 and 2025 tax returns and verify if their total household income meets our 2026 debt-to-income requirements?",
    "user_id": "test-user"
  }
}
EOF
```

```sh
# show logs for iap audit errors (bulletproof type-safe projection)
gcloud logging read 'severity=ERROR AND labels."iap.googleapis.com/audited_resource_type":"agentregistry.googleapis.com"' \
  --project=${PROJECT_ID} \
  --limit=20 \
  --format=json | jq -r '
    ["TIMESTAMP", "PRINCIPAL_SUBJECT", "HTTP_REQUEST_HOST", "REGISTRY_ID"],
    (.[] | [
      ((.timestamp // "") | split(".")[0] + "Z"),
      ((.protoPayload.authenticationInfo.principalSubject // "") | split("/") | .[-2:] | join("/")),
      ((.protoPayload.request.httpRequest.url // "") | split("/")[2] // ""),
      ((.protoPayload.resourceName // "") | split("/") | .[-2:] | join("/"))
    ]) | @tsv' | column -t -s $'\t'
```

```log
TIMESTAMP             PRINCIPAL_SUBJECT                     HTTP_REQUEST_HOST                        REGISTRY_ID
2026-05-17T14:55:30Z  reasoningEngines/${REASONING_ENGINE_ID}  telemetry.mtls.googleapis.com               endpoints/agentregistry-00000000-0000-0000-37df-69394c5eff76
2026-05-17T14:55:29Z  reasoningEngines/${REASONING_ENGINE_ID}  aiplatform.mtls.googleapis.com              endpoints/agentregistry-00000000-0000-0000-8707-f90fa41134b8
2026-05-17T14:55:29Z  reasoningEngines/${REASONING_ENGINE_ID}  iamcredentials.mtls.googleapis.com          endpoints/agentregistry-00000000-0000-0000-951f-d0cb7bcea856
2026-05-17T14:55:29Z  reasoningEngines/${REASONING_ENGINE_ID}  iamcredentials.mtls.googleapis.com          endpoints/agentregistry-00000000-0000-0000-951f-d0cb7bcea856
2026-05-17T14:55:29Z  reasoningEngines/${REASONING_ENGINE_ID}  iamcredentials.mtls.googleapis.com          endpoints/agentregistry-00000000-0000-0000-951f-d0cb7bcea856
2026-05-17T12:06:00Z  reasoningEngines/${REASONING_ENGINE_ID}  us-central1-aiplatform.mtls.googleapis.com  endpoints/agentregistry-00000000-0000-0000-0bb3-dd8fd9f9f1c9
```

```sh
# lookup endpoint by uuid
gcloud alpha agent-registry endpoints list \
  --project=${PROJECT_ID} --location=${REGION} \
  --filter="name:'agentregistry-00000000-0000-0000-37df-69394c5eff76'"
```

```log
TIMESTAMP             PRINCIPAL_SUBJECT                     HTTP_REQUEST_HOST                        REGISTRY_ID
2026-05-17T15:26:53Z  reasoningEngines/${REASONING_ENGINE_ID}  corporate-email-${HASH}-uc.a.run.app  mcpServers/agentregistry-00000000-0000-0000-85cc-bd757ea63fd1
2026-05-17T15:26:21Z  reasoningEngines/${REASONING_ENGINE_ID}  corporate-email-${HASH}-uc.a.run.app  mcpServers/agentregistry-00000000-0000-0000-85cc-bd757ea63fd1
2026-05-17T15:25:48Z  reasoningEngines/${REASONING_ENGINE_ID}  corporate-email-${HASH}-uc.a.run.app  mcpServers/agentregistry-00000000-0000-0000-85cc-bd757ea63fd1
2026-05-17T15:25:16Z  reasoningEngines/${REASONING_ENGINE_ID}  corporate-email-${HASH}-uc.a.run.app  mcpServers/agentregistry-00000000-0000-0000-85cc-bd757ea63fd1
2026-05-17T15:24:45Z  reasoningEngines/${REASONING_ENGINE_ID}  corporate-email-${HASH}-uc.a.run.app  mcpServers/agentregistry-00000000-0000-0000-85cc-bd757ea63fd1
2026-05-17T15:24:12Z  reasoningEngines/${REASONING_ENGINE_ID}  corporate-email-${HASH}-uc.a.run.app  mcpServers/agentregistry-00000000-0000-0000-85cc-bd757ea63fd1
```

```sh
# lookup mcp server by uuid
gcloud alpha agent-registry mcp-servers list \
  --project=${PROJECT_ID} --location=${REGION} \
  --filter="name:'agentregistry-00000000-0000-0000-85cc-bd757ea63fd1'"
```

> [!note]
> conditional deny for corporate email expected

> [!warning]
> however it does not appear that policies in place to support enforced mode... need to grant roles on _ENDPOINTS_

```sh
# set agent identity
export RE_AGENT_PRINCIPAL="principal://agents.global.org-${ORG_ID}.system.id.goog/resources/aiplatform/projects/${PROJECT_NUMBER}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}"
echo ${RE_AGENT_PRINCIPAL}
```

```sh
# fetch agent identity
export RE_RE_AGENT_PRINCIPAL=$(gcloud alpha agent-registry agents list \
  --project=${PROJ_ID} --location=${REGION} --filter="displayName=${AGENT_NAME}" \
  --format="value(attributes.'agentregistry.googleapis.com/system/RuntimeIdentity'.principal)")
echo ${RE_RE_AGENT_PRINCIPAL}
```

> [!caution]
> for endpoints...

```sh
# set endpoint registry uid (from logs)
export TARGET_REG_EP_UID="agentregistry-00000000-0000-0000-85cc-bd757ea63fd1"
echo ${TARGET_REG_EP_UID}
```

```sh
# fetch etag
export IAP_ETAG=$(curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/endpoints/${TARGET_REG_EP_UID}:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
  -d '{}' | jq -r '.etag')
echo "Active Etag: ${IAP_ETAG}"
```

```sh
# post policy grant for agent iap egressor role on endpoint
curl -s -X POST "https://iap.googleapis.com/v1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/endpoints/${TARGET_REG_EP_UID}:setIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJECT_ID}" \
-d @- <<EOF
{
  "policy": {
    "etag": "${IAP_ETAG}",
    "bindings": [
      {
        "role": "roles/iap.egressor",
        "members": ["${RE_AGENT_PRINCIPAL}"]
      }
    ]
  }
}
EOF
```

```sh
# get iap policy for target >> @ registry ${location} : endpoint (iam v1)
curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/endpoints/${TARGET_REG_EP_UID}:getIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
-d '{"options":{"requestedPolicyVersion":3}}' | jq .
```


> [!caution]
> for mcp servers...

```sh
# set mcp registry uid (from logs)
export TARGET_REG_MCP_UID="agentregistry-00000000-0000-0000-85cc-bd757ea63fd1"
echo ${TARGET_REG_MCP_UID}
```

```sh
# get iap policy for target >> @ registry ${location} : mcp-servers (iam v3)
curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/mcpServers/${TARGET_REG_MCP_UID}:getIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
-d '{"options":{"requestedPolicyVersion":3}}' | jq .
```

> [!note]
> this would be the single shot option

```sh
# grant roles/iap.egressor on all registered endpoints (individually)
./scripts/grant_agent_mcp_egress.sh \
  --endpoints \
  --agent-id ${RE_ENGINE_ID}
```

## (16) ge test

```sh
# set vars
export LOCATION="global"
export GE_APP_NAME="Mortgage Assistant"
echo ${LOCATION}
echo ${GE_APP_NAME}
```

```sh
# fetch ge app id
export GE_APP_ID=$(curl -s -X GET "https://${LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/engines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJECT_ID}" \
  | jq -r --arg name "${GE_APP_NAME}" '.engines[] | select(.displayName==$name) | .name | split("/") | last')
echo ${GE_APP_ID}
```

```sh
# register re adk agent with gemini ent (skipping authorizations)
curl -s -X POST "https://${LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${GE_APP_ID}/assistants/default_assistant/agents" \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJECT_ID}" \
-d @- <<EOF
{
  "name": "projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${GE_APP_ID}",
  "displayName": "Mortgage Assistant Agent",
  "description": "ADK mortgage assistant agent connecting to legacy DMS, income verification, and corporate email services.",
  "adkAgentDefinition": {
    "provisionedReasoningEngine": {
      "reasoningEngine": "projects/${PROJECT_NUMBER}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}"
    }
  },
  "authorizationConfig": {
    "agentAuthorization": "",
    "toolAuthorizations": []
  },
  "sharingConfig": {
    "scope": "ALL_USERS"
  },
  "observabilityConfig": {
    "observabilityEnabled": true,
    "sensitiveLoggingEnabled": true
  },
  "agentInvocationSpec": {
    "description": "",
    "invocationMode": "AUTOMATIC"
  }
}
EOF
```

```sh
# verify agent registration
curl -s -X GET "https://${LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/engines" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" -H "X-Goog-User-Project: ${PROJECT_ID}" \
| jq -r --arg name "${GE_APP_NAME}" '.engines[] | select(.displayName==$name)'
```

```sh
# verify iam role bindings for discovery engine service agent
gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

## (17) o11y dashboard

```sh
# navidate to custom dashboard in console ui...
echo "https://console.cloud.google.com/monitoring/dashboards"
```

## (18) troubleshooting

<!-- ```sh
# get gemini cli from binfs by adding alias to bashrc
echo "alias gemini='/google/bin/releases/gemini-cli/tools/gemini'" >> ~/.bashrc
source ~/.bashrc
source env.sh
``` -->

```sh
# start gemini cli (in ../cloud-networking-solutions/demos/agent-gateway)
gemini
```

```sh
# list skills
/skills list
```

# resync

```sh
# reload env vars (start at project root)
source env.sh
```

```sh
# change dir
cd ../cloud-networking-solutions

# fetch latest code
git pull
```

```sh
# change dir
cd ../demos/agent-gateway/terraform

# apply tf
terraform apply
```

```sh
# change dir (to ../agent-gateway)
cd ..

# redeploy with skaffold
skaffold run
```

> policies

```sh
# show logs for iap audit errors (bulletproof type-safe projection)
gcloud logging read 'severity=ERROR AND labels."iap.googleapis.com/audited_resource_type":"agentregistry.googleapis.com"' \
  --project=${PROJECT_ID} \
  --limit=10 \
  --format=json | jq -r '
    ["TIMESTAMP", "PRINCIPAL_SUBJECT", "HTTP_REQUEST_HOST", "REGISTRY_ID"],
    (.[] | [
      ((.timestamp // "") | split(".")[0] + "Z"),
      ((.protoPayload.authenticationInfo.principalSubject // "") | split("/") | .[-2:] | join("/")),
      ((.protoPayload.request.httpRequest.url // "") | split("/")[2] // ""),
      ((.protoPayload.resourceName // "") | split("/") | .[-2:] | join("/"))
    ]) | @tsv' | column -t -s $'\t'
```

```log
TIMESTAMP             PRINCIPAL_SUBJECT                     HTTP_REQUEST_HOST                         REGISTRY_ID
2026-05-19T15:28:42Z                                        cloudresourcemanager.mtls.googleapis.com  unregisteredEndpoint
2026-05-19T15:28:42Z  reasoningEngines/${REASONING_ENGINE_ID}  telemetry.googleapis.com                  endpoints/agentregistry-00000000-0000-0000-6955-21a9b3d57e37
2026-05-19T15:28:42Z  reasoningEngines/${REASONING_ENGINE_ID}  agentregistry.googleapis.com              endpoints/agentregistry-00000000-0000-0000-0606-da5fc2fe95dc
```

```sh
# lookup endpoint by uuid
gcloud alpha agent-registry endpoints list \
  --project=${PROJECT_ID} --location=${REGION} \
  --filter="name:'agentregistry-00000000-0000-0000-6955-21a9b3d57e37'"
```

```sh
# list registry services (region)
gcloud alpha agent-registry services list \
  --project=${PROJECT_ID} --location=${REGION} \
  --format="table(displayName,interfaces.url)"

gcloud alpha agent-registry endpoints list \
  --project=${PROJECT_ID} --location=${REGION} \
  --format="table(displayName,interfaces.url)"

# list registry services (global)
gcloud alpha agent-registry services list \
  --project=${PROJECT_ID} --location=global \
  --format="table(displayName,interfaces.url)"
```

```sh
# lookup endpoint details by hostname substring (regional)
gcloud alpha agent-registry endpoints list \
  --project=${PROJECT_ID} \
  --location=${REGION} \
  --filter="interfaces.url:cloudresourcemanager.mtls" \
  --format="table(displayName, name.basename(), interfaces[0].url)"
```

```sh
# lookup endpoint details by hostname substring (global)
gcloud alpha agent-registry endpoints list \
  --project=${PROJECT_ID} \
  --location=global \
  --filter="interfaces.url:cloudresourcemanager.mtls" \
  --format="table(displayName, name.basename(), interfaces[0].url)"
```

## endpoints

```sh
# set endpoint registry uid (from logs)
export TARGET_REG_EP_UID="agentregistry-00000000-0000-0000-8763-5f321815b4b5"
echo ${TARGET_REG_EP_UID}
```

```sh
# set agent identity
export RE_AGENT_PRINCIPAL="principal://agents.global.org-${ORG_ID}.system.id.goog/resources/aiplatform/projects/${PROJECT_NUMBER}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}"
echo ${RE_AGENT_PRINCIPAL}
```

```sh
# fetch etag
export IAP_ETAG=$(curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/endpoints/${TARGET_REG_EP_UID}:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
  -d '{}' | jq -r '.etag')
echo "Active Etag: ${IAP_ETAG}"
```

```sh
# post policy grant for agent iap egressor role on endpoint
curl -s -X POST "https://iap.googleapis.com/v1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/endpoints/${TARGET_REG_EP_UID}:setIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJECT_ID}" \
-d @- <<EOF
{
  "policy": {
    "etag": "${IAP_ETAG}",
    "bindings": [
      {
        "role": "roles/iap.egressor",
        "members": ["${RE_AGENT_PRINCIPAL}"]
      }
    ]
  }
}
EOF
```

```sh
# get iap policy for target >> @ registry ${location} : endpoint (iam v1)
curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/endpoints/${TARGET_REG_EP_UID}:getIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
-d '{"options":{"requestedPolicyVersion":3}}' | jq .
```


> [!caution]
> for mcp servers...

```sh
# set mcp registry uid (from logs)
export TARGET_REG_MCP_UID="agentregistry-00000000-0000-0000-85cc-bd757ea63fd1"
echo ${TARGET_REG_MCP_UID}
```

```sh
# get iap policy for target >> @ registry ${location} : mcp-servers (iam v3)
curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/mcpServers/${TARGET_REG_MCP_UID}:getIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
-d '{"options":{"requestedPolicyVersion":3}}' | jq .
```

> for cloud resource manager (global)

```sh
# register the base cloud resource manager service globally
gcloud alpha agent-registry services create "cloudresourcemanager" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="Cloud Resource Manager" \
  --endpoint-spec-type=no-spec \
  --interfaces="url=https://cloudresourcemanager.googleapis.com,protocolBinding=JSONRPC"
```

```sh
# register the mtls cloud resource manager service globally
gcloud alpha agent-registry services create "cloudresourcemanager-mtls" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="Cloud Resource Manager mTLS" \
  --endpoint-spec-type=no-spec \
  --interfaces="url=https://cloudresourcemanager.mtls.googleapis.com,protocolBinding=JSONRPC"
```

```sh
# fetch new global uuid
gcloud alpha agent-registry endpoints list \
  --project=${PROJECT_ID} \
  --location=global \
  --filter="interfaces.url:cloudresourcemanager.mtls" \
  --format="table(displayName, name.basename())"
```

```sh
# set endpoint registry uid (from logs)
export TARGET_REG_EP_UID="agentregistry-00000000-0000-0000-8763-5f321815b4b5"
echo ${TARGET_REG_EP_UID}
```

```sh
# set endpoint registry location
export LOCATION="global"
echo ${LOCATION}

# fetch etag
export IAP_ETAG=$(curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/${LOCATION}/iap_web/agentRegistry/endpoints/${TARGET_REG_EP_UID}:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
  -d '{}' | jq -r '.etag')
echo "Active Etag: ${IAP_ETAG}"
```

```sh
# post policy grant for agent iap egressor role on endpoint
curl -s -X POST "https://iap.googleapis.com/v1/projects/${PROJECT_NUMBER}/locations/${LOCATION}/iap_web/agentRegistry/endpoints/${TARGET_REG_EP_UID}:setIamPolicy" \
-H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
-H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJECT_ID}" \
-d @- <<EOF
{
  "policy": {
    "etag": "${IAP_ETAG}",
    "bindings": [
      {
        "role": "roles/iap.egressor",
        "members": ["${RE_AGENT_PRINCIPAL}"]
      }
    ]
  }
}
EOF
```

```sh
# change dir
cd src/mortgage-agent

# install dependencies
uv sync

# single shot upgrade via environment variable
uv run python deploy_agent.py \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --enable-agent-identity \
  --agent-name="mortgage-agent" \
  --agent-gateway=projects/${PROJECT_ID}/locations/${REGION}/agentGateways/agent-gateway \
  --mcp-invoker-sa=$(terraform -chdir=../../terraform output -raw agent_mcp_invoker_email) \
  --model-endpoint-location=global \
  --update=projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${RE_ENGINE_ID}
```

## mcp

```sh
# set target mcp server uuid for corporate-email
export TARGET_REG_MCP_UID=$(gcloud alpha agent-registry mcp-servers list \
  --project=${PROJECT_ID} \
  --location=${REGION} \
  --filter="displayName='corporate-email'" \
  --format="value(name.basename())")
echo ${TARGET_REG_MCP_UID}

# fetch the active etag
export IAP_ETAG=$(curl -s -X POST "https://iap.googleapis.com/v1beta1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/mcpServers/${TARGET_REG_MCP_UID}:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" -H "Content-Type: application/json" \
  -d '{"options":{"requestedPolicyVersion":3}}' | jq -r '.etag')
echo ${IAP_ETAG}

# get iam policy
curl -s -X POST "https://iap.googleapis.com/v1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/mcpServers/${TARGET_REG_MCP_UID}:getIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJECT_ID}" -d '{"options":{"requestedPolicyVersion":3}}' | jq .

# apply smart conditional policy (allowing tools/list and read-only tools)
curl -s -X POST "https://iap.googleapis.com/v1/projects/${PROJECT_NUMBER}/locations/${REGION}/iap_web/agentRegistry/mcpServers/${TARGET_REG_MCP_UID}:setIamPolicy" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "Content-Type: application/json" -H "X-Goog-User-Project: ${PROJECT_ID}" \
  -d @- <<EOF
{
  "policy": {
    "version": 3,
    "etag": "${IAP_ETAG}",
    "bindings": [
      {
        "role": "roles/iap.egressor",
        "members": ["${RE_AGENT_PRINCIPAL}"],
        "condition": {
          "title": "ReadOnlyAndDiscoveryOnly",
          "description": "Allows tool discovery and restricts execution to read-only tools",
          "expression": "api.getAttribute('iap.googleapis.com/mcp.toolName', '') == '' || api.getAttribute('iap.googleapis.com/mcp.tool.isReadOnly', false) == true"
        }
      }
    ]
  }
}
EOF
```

> before, fyi

```log
{
  "version": 3,
  "etag": "BwZSLxlhzOs=",
  "bindings": [
    {
      "role": "roles/iap.egressor",
      "members": [
        "principal://agents.global.org-${ORG_ID}.system.id.goog/resources/aiplatform/projects/${PROJECT_NO}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}"
      ],
      "condition": {
        "title": "ReadOnlyToolsOnly",
        "description": "Restrict ${REASONING_ENGINE_ID} to read-only tools on corporate-email",
        "expression": "api.getAttribute('iap.googleapis.com/mcp.tool.isReadOnly', false) == true"
      }
    }
  ]
}
```

## test

> initial prompt

```
I am reviewing the Sterling familys current application. Can you summarize their 2024 and 2025 tax returns and verify if their total household income meets our 2026 debt-to-income requirements?
```

> follow-up prompt

```
Can you send a summary of this to my email jane@example.com
```

