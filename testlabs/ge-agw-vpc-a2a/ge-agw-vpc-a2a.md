---
lab: ge-agw-vpc-a2a
---

# ge agent gateway vpc a2a

## setup

```sh
source env.sh
```

```sh
# enable google apis (agent platform bundle, part 1)
gcloud services enable \
  agentregistry.googleapis.com \
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
  notebooks.googleapis.com \
  observability.googleapis.com
```

```sh
# enable google apis (agent platform bundle, part 2)
gcloud services enable \
  securitycenter.googleapis.com \
  saasservicemgmt.googleapis.com \
  storage.googleapis.com \
  telemetry.googleapis.com \
  texttospeech.googleapis.com
```

```sh
# enable google apis (all the rest)
gcloud services enable \
  certificatemanager.googleapis.com \
  orgpolicy.googleapis.com
```

```sh
# create dirs for certs and configs
mkdir -p certs cfg
```

## network

```sh
# set vars for ip addresses
export PSC_IP="240.0.0.10"
export VM_IP="10.10.20.22"
export ILB_IP="10.10.30.88"

echo ${PSC_IP}
echo ${VM_IP}
echo ${ILB_IP}
```

```sh
# create vpc network
gcloud compute networks create vnet-${PROJ_SLUG} --subnet-mode=custom
```

### subnets

```sh
# create subnet for agent gateway psc na
gcloud compute networks subnets create subnet-${REGION}-agw \
  --network=vnet-${PROJ_SLUG} \
  --range=192.168.10.0/28 \
  --region=${REGION} \
  --enable-private-ip-google-access

# create subnet for cloud run dvpc egress
gcloud compute networks subnets create subnet-${REGION}-crun \
  --network=vnet-${PROJ_SLUG} \
  --range=10.10.10.0/24 \
  --region=${REGION} \
  --enable-private-ip-google-access

# create subnet for vms
gcloud compute networks subnets create subnet-${REGION}-vm \
  --network=vnet-${PROJ_SLUG} \
  --range=10.10.20.0/24 \
  --region=${REGION} \
  --enable-private-ip-google-access

# create subnet for frontends
gcloud compute networks subnets create subnet-${REGION}-fe \
  --network=vnet-${PROJ_SLUG} \
  --range=10.10.30.0/24 \
  --region=${REGION} \
  --enable-private-ip-google-access

# create subnet for proxy ilb
gcloud compute networks subnets create subnet-${REGION}-proxy \
  --purpose=REGIONAL_MANAGED_PROXY \
  --role=ACTIVE \
  --network=vnet-${PROJ_SLUG} \
  --range=10.10.40.0/24 \
  --region=${REGION}
```

### fw

```sh
# create fw policy
gcloud compute network-firewall-policies create fw-policy-${PROJ_SLUG} --global
```

```sh
# create fw policy rules
gcloud compute network-firewall-policies rules create 1001 \
  --description="allow all out and log" \
  --firewall-policy=fw-policy-${PROJ_SLUG} \
  --global-firewall-policy \
  --action=allow \
  --direction=EGRESS \
  --layer4-configs=all \
  --dest-ip-ranges=0.0.0.0/0 \
  --enable-logging

gcloud compute network-firewall-policies rules create 2001 \
  --description="allow in ssh from iap" \
  --firewall-policy=fw-policy-${PROJ_SLUG} \
  --global-firewall-policy \
  --action=allow \
  --direction=INGRESS \
  --layer4-configs=tcp:22  \
  --src-ip-ranges=35.235.240.0/20
```

```sh
# associate fw policy to vpc network
gcloud compute network-firewall-policies associations create \
  --name=fw-policy-bind-${PROJ_SLUG} \
  --firewall-policy=fw-policy-${PROJ_SLUG} \
  --network=vnet-${PROJ_SLUG} \
  --global-firewall-policy
```

### psc

```sh
# create psc network attachment
gcloud compute network-attachments create psc-na-${REGION}-agw \
  --region=${REGION} \
  --subnets=subnet-${REGION}-agw \
  --connection-preference=ACCEPT_AUTOMATIC
```

```sh
# show psc network attachment details
gcloud compute network-attachments describe psc-na-${REGION}-agw --region=${REGION}
```

```sh
# fetch psc na uri
export PSC_NA_URI=$(gcloud compute network-attachments describe psc-na-${REGION}-agw \
  --region=${REGION} \
  --format="value(selfLink.scope(v1))")
echo ${PSC_NA_URI}
```

```sh
# reserve internal global ipv4 address
gcloud compute addresses create ip-psc2gapis \
  --global \
  --purpose=PRIVATE_SERVICE_CONNECT \
  --addresses=${PSC_IP} \
  --network=vnet-${PROJ_SLUG}
```

```sh
# create psc endpoint for google apis
gcloud compute forwarding-rules create psc2gapis \
  --global \
  --network=vnet-${PROJ_SLUG} \
  --address=ip-psc2gapis \
  --target-google-apis-bundle=all-apis
```

```sh
# show psc endpoint details
gcloud compute forwarding-rules describe psc2gapis --global
```

### dns

```sh
# create private dns zone
gcloud dns managed-zones create zone-run-app \
  --description="private zone for run-app" \
  --dns-name="run.app." \
  --visibility=private \
  --networks=vnet-${PROJ_SLUG}
```

```sh
# create dns record
gcloud dns record-sets create *.run.app \
  --zone=zone-run-app \
  --type=A \
  --ttl=300 \
  --rrdatas=${PSC_IP}
```

```sh
# create private zone
gcloud dns managed-zones create zone-${DOMAIN_RESOURCE} \
  --description="private zone for ${DOMAIN_RESOURCE}" \
  --dns-name=${HOSTNAME} \
  --networks=vnet-${PROJ_SLUG} \
  --visibility=private
```

```sh
# create records
gcloud dns record-sets create ${HOSTNAME} \
  --zone=zone-${DOMAIN_RESOURCE} \
  --type=A \
  --ttl=300 \
  --rrdatas=${ILB_IP}
```

```sh
# create dns policy (logging)
gcloud dns policies create dns-policy-${PROJ_SLUG} \
  --description="dns logging for vnet-${PROJ_SLUG}" \
  --networks=vnet-${PROJ_SLUG} \
  --enable-logging
```

## gateway

```sh
# create new agent gateway config file (with network settings)
cat > cfg/${AGW_NAME}-networkConfig.yaml << EOF
name: ${AGW_NAME}
protocols:
  - MCP
googleManaged:
  governedAccessPath: AGENT_TO_ANYWHERE
registries:
  - "//agentregistry.googleapis.com/projects/${PROJ_ID}/locations/${REGION}"
networkConfig:
  egress:
    networkAttachment: ${PSC_NA_URI}
  dnsPeeringConfig:
    domains:
      - run.app.
      - ${HOSTNAME}.
    targetProject: ${PROJ_ID}
    targetNetwork: projects/${PROJ_ID}/global/networks/vnet-${PROJ_SLUG}
EOF
```

```sh
# import agent gateway config file (create gateway)
gcloud network-services agent-gateways import ${AGW_NAME} \
  --source="cfg/${AGW_NAME}-networkConfig.yaml" \
  --location=${REGION}
```

```sh
# list agent gateways (in region)
gcloud network-services agent-gateways list --location=${REGION}

# show agent gateway details
gcloud network-services agent-gateways describe ${AGW_NAME} --location=${REGION}
```

```sh
# show psc network attachment details
gcloud compute network-attachments describe psc-na-${REGION}-agw --region=${REGION}
```

## codebase

```bash
# clone remote repository to temp local dir
git clone https://github.com/miclarso/public.git ./temp_ge_agw_vpc_a2a
```

```bash
# copy repo folders to working project dir
cp -r temp_ge_agw_vpc_a2a/devlabs/ge-agw-vpc-a2a/agent-decode ./agent-decode
cp -r temp_ge_agw_vpc_a2a/devlabs/ge-agw-vpc-a2a/mcp-math ./mcp-math
```

```bash
# remove temporary directory
rm -rf temp_ge_agw_vpc_a2a
```

```sh
# create bin for config files
mkdir -p cfg
```

## org policy

to allow `allUsers` ingress on cloud run (disable org policy constraint on project)

```sh
# create policy file
cat << EOF > cfg/drs_project_policy.yaml
name: projects/${PROJ_NO}/policies/iam.allowedPolicyMemberDomains
spec:
  rules:
  - allowAll: true
EOF
```

```sh
# apply policy
gcloud org-policies set-policy cfg/drs_project_policy.yaml --project=${PROJ_ID}
```

```sh
# verify the project specific override was saved
gcloud org-policies describe iam.allowedPolicyMemberDomains --project=${PROJ_ID}
```

```sh
# check the effective policy currently enforced on the project (including inherited rules)
gcloud org-policies describe iam.allowedPolicyMemberDomains --project=${PROJ_ID} --effective
```

## test vm

```sh
# create startup file
cat > cfg/startup-vm-${PROJ_SLUG}.sh << EOF
#! /bin/bash
apt-get install dnsutils -yq
EOF
```

```sh
# create vm instance
gcloud compute instances create vm-${PROJ_SLUG} \
  --zone=${ZONE} \
  --machine-type=e2-micro \
  --subnet=subnet-${REGION}-vm \
  --no-address \
  --private-network-ip=${VM_IP} \
  --scopes=cloud-platform \
  --shielded-secure-boot \
  --metadata-from-file=startup-script=cfg/startup-vm-${PROJ_SLUG}.sh
```

```sh
# test vm
gcloud compute ssh vm-${PROJ_SLUG} --zone=${ZONE} \
  --command="dig +noall +answer ${HOSTNAME}"
```

## iam (pre deploy)

```sh
# grant cloud run builder role to default compute sa
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="serviceAccount:${PROJ_NO}-compute@developer.gserviceaccount.com" \
  --role="roles/run.builder"
```

```sh
# show iam policy on project for default compute sa
gcloud projects get-iam-policy ${PROJ_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members=serviceAccount:${PROJ_NO}-compute@developer.gserviceaccount.com" \
  --format="table(bindings.role:label=ROLE, bindings.members:label=PRINCIPAL_IDENTITY)"
```

## a2a agent

```sh
# deploy agent
gcloud run deploy agent-${AGENT_SLUG} \
  --source=./agent-${AGENT_SLUG}/agent \
  --set-env-vars="AGENT_A2A_URL=${AGENT_A2A_URL}" \
  --ingress=internal-and-cloud-load-balancing \
  --allow-unauthenticated \
  --network=vnet-${PROJ_SLUG} \
  --subnet=subnet-${REGION}-crun \
  --vpc-egress=all-traffic \
  --region=${REGION}
```

```sh
# create agent card json
PYTHONPATH=${AGENT_NAME}/agent python3 -c "
import sys, os, json
from unittest.mock import MagicMock
for m in ['fastapi', 'fastapi.responses', 'uvicorn']:
    sys.modules[m] = MagicMock()
import agent
print(json.dumps(agent.AGENT_CARD, indent=2))
" > ${AGENT_NAME}/agent.json
```

```sh
# view agent card json
cat ${AGENT_NAME}/agent.json | jq .
``` 

## mcp server

```sh
# deploy cloud run service
gcloud -q run deploy ${MCP_NAME} \
  --source=${MCP_NAME}/server \
  --region=${REGION} \
  --ingress=internal \
  --allow-unauthenticated \
  --network=vnet-${PROJ_SLUG} \
  --subnet=subnet-${REGION}-crun \
  --vpc-egress=all-traffic \
  --startup-probe=httpGet.path=/warmup
```

## iam (post deploy)

for ge calling a2a agent...

```sh
# allow unauthenticated invocation
gcloud run services add-iam-policy-binding --region=${REGION} --member=allUsers --role=roles/run.invoker ${AGENT_NAME}
gcloud run services add-iam-policy-binding --region=${REGION} --member=allUsers --role=roles/run.invoker ${MCP_NAME}
```

for generating toolspec...

```sh
# grant run invoker role to user account on cloud run service level
gcloud run services add-iam-policy-binding ${MCP_NAME} \
  --region=${REGION} \
  --member="user:${USER_IDENTITY}" \
  --role="roles/run.invoker"
```

```sh
# show iam policy on cloud run service for invoker role (verify bindings)
gcloud run services get-iam-policy ${MCP_NAME} \
  --region=${REGION} \
  --flatten="bindings[].members" \
  --filter="bindings.role=roles/run.invoker" \
  --format="table(bindings.members:label=PRINCIPAL_IDENTITY, bindings.role:label=ROLE)"
```

## certificate

```sh
# create self signed cert
openssl req -x509 \
  -newkey rsa:2048 \
  -nodes \
  -days 3650 \
  -keyout certs/${PREFIX}-key.pem \
  -out certs/${PREFIX}-cert.pem \
  -subj "/CN=${HOSTNAME}" \
  -addext "subjectAltName=DNS:${HOSTNAME}"
```

```sh
# upload certs to certificate manager
gcloud certificate-manager certificates create cert-${PREFIX} \
  --project=${PROJ_ID} \
  --certificate-file=certs/${PREFIX}-cert.pem \
  --private-key-file=certs/${PREFIX}-key.pem \
  --location=${REGION}
```

## ilb

```sh
# reserve ip
gcloud compute addresses create ip-ilb-ai \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --subnet="projects/${PROJ_ID}/regions/${REGION}/subnetworks/subnet-${REGION}-fe" \
  --purpose=SHARED_LOADBALANCER_VIP \
  --addresses=${ILB_IP}
```

```sh
# create serverless negs
gcloud compute network-endpoint-groups create neg-s8s-${AGENT_NAME} \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --network-endpoint-type=serverless \
  --cloud-run-service="${AGENT_NAME}"
```

```sh
# create regional backend services
gcloud compute backend-services create bes-s8s-${AGENT_NAME} \
  --project=${PROJ_ID} \
  --load-balancing-scheme=INTERNAL_MANAGED \
  --protocol=HTTP \
  --region=${REGION}
```

```sh
# add serverless negs to backend services
gcloud compute backend-services add-backend bes-s8s-${AGENT_NAME} \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --network-endpoint-group=neg-s8s-${AGENT_NAME} \
  --network-endpoint-group-region=${REGION}
```

```sh
# create regional url map
gcloud compute url-maps create ilb-${PREFIX} \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --default-service=projects/${PROJ_ID}/regions/${REGION}/backendServices/bes-s8s-${AGENT_NAME}
```

```sh
# create regional url map import file
FP=$(gcloud compute url-maps describe ilb-${PREFIX} --region=${REGION} --format="value(fingerprint)")
cat > cfg/ilb-${PREFIX}-url-map.yaml << EOF
name: ilb-${PREFIX}
fingerprint: ${FP}
defaultService: https://www.googleapis.com/compute/v1/projects/${PROJ_ID}/regions/${REGION}/backendServices/bes-s8s-${AGENT_NAME}
hostRules:
  - hosts:
      - "${HOSTNAME}"
    pathMatcher: agent-matcher
pathMatchers:
  - name: agent-matcher
    defaultService: https://www.googleapis.com/compute/v1/projects/${PROJ_ID}/regions/${REGION}/backendServices/bes-s8s-${AGENT_NAME}
    pathRules:
      # --- for 1st ai.<whatever> ---
      - paths:
          - "/agent-${AGENT_NAME}"
          - "/agent-${AGENT_NAME}/*"
        service: https://www.googleapis.com/compute/v1/projects/${PROJ_ID}/regions/${REGION}/backendServices/bes-s8s-${AGENT_NAME}
        routeAction:
          urlRewrite:
            pathPrefixRewrite: "/"
EOF
```

for later if/when add more agents or mcp servers or endpoints behind load balancer...

```sh
      # --- for 2nd ai.<whatever> ---
      - paths:
          - "/${TBD}"
          - "/${TBD}/*"
        service: https://www.googleapis.com/compute/v1/projects/${PROJ_ID}/regions/${REGION}/backendServices/bes-s8s-${TBD}
        routeAction:
          urlRewrite:
            pathPrefixRewrite: "/"

      # --- for 3rd ai.<whatever> ---
      - paths:
          - "/${TBD}"
          - "/${TBD}/*"
        service: https://www.googleapis.com/compute/v1/projects/${PROJ_ID}/regions/${REGION}/backendServices/bes-s8s-${TBD}
        routeAction:
          urlRewrite:
            pathPrefixRewrite: "/"
EOF
```

```sh
# show config file
cat cfg/ilb-${PREFIX}-url-map.yaml
```

```sh
# import regional url map configuration
gcloud compute url-maps import ilb-${PREFIX} \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --source=cfg/ilb-${PREFIX}-url-map.yaml \
  --quiet
```

```sh
# create regional target https proxy
gcloud compute target-https-proxies create proxy-${PREFIX} \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --url-map=ilb-${PREFIX} \
  --certificate-manager-certificates=cert-${PREFIX}
```

```sh
# create regional forwarding rule
gcloud compute forwarding-rules create fr-${PREFIX} \
  --project=${PROJ_ID} \
  --region=${REGION} \
  --load-balancing-scheme=INTERNAL_MANAGED \
  --network="projects/${PROJ_ID}/global/networks/vnet-${PROJ_SLUG}" \
  --subnet="projects/${PROJ_ID}/regions/${REGION}/subnetworks/subnet-${REGION}-fe" \
  --address=ip-ilb-${PREFIX} \
  --target-https-proxy=proxy-${PREFIX} \
  --target-https-proxy-region=${REGION} \
  --ports=443
```

## test

```sh
# test agent card fetch (from internal vm)
gcloud compute ssh vm-${PROJ_SLUG} --zone=${ZONE} \
  --command="curl -k -s https://${HOSTNAME}/${AGENT_NAME}/.well-known/agent.json | jq ."
```

```sh
# create test request payload
cat > cfg/req-send-message.json << EOF
{
  "jsonrpc": "2.0",
  "id": "test-2",
  "method": "tasks.send_message",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "blueberry pancakes"
        }
      ]
    }
  }
}
EOF
```

```sh
# test a2a agent invocation (stream payload via ssh command)
gcloud compute ssh vm-${PROJ_SLUG} --zone=${ZONE} \
  --command="curl -k -s -X POST 'https://${HOSTNAME}/${AGENT_NAME}/tasks/send-message' -H 'Content-Type: application/json' -d @-" < cfg/req-send-message.json | jq .
```

## registry

