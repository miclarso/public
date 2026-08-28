---
lab: agw-codelab
ver: private connectivity
rev: 01
---

# agent gateway

> [!important]
> run public networking first ... see [`agw-codelab-pub.md`](agw-codelab-pub.md)

## (1) about

_Governing agentic workloads with Agent Gateway on Gemini Enterprise Agent Platform_
- https://codelabs.developers.google.com/cloudnet-agent-gateway#0

## (2) setup

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

## (5) public dns

```sh
# create public dns zone
gcloud dns managed-zones create agw-example-com \
  --dns-name="${DOMAIN_NAME}." \
  --description="Public zone for ${DOMAIN_NAME}" \
  --visibility=public
```

## (6) tf vars

```sh
# change dir (../)
cd agent-gateway
```

```sh
# toggle private networking switch
sed -i 's/enable_cloud_run_private_networking = false/enable_cloud_run_private_networking = true/' terraform/terraform.tfvars

# update public dns zone domain
sed -i "s/dns_zone_domain = \"demo.example.com.\"/dns_zone_domain = \"${DOMAIN_NAME}.\"/" terraform/terraform.tfvars

# update internal mcp domains (updates both mcp_internal_dns_zone and psc_interface_dns_zone)
sed -i "s/domain = \"mcp.demo.example.com.\"/domain = \"mcp.${DOMAIN_NAME}.\"/" terraform/terraform.tfvars
```

```sh
# verify config values
grep -E "^(enable_cloud_run_private_networking|dns_zone_domain|  domain)" terraform/terraform.tfvars
```

## (7) tf deploy

```sh
# apply tf
terraform -chdir=terraform apply
```




