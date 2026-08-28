# ge-agw-vpc-a2a env vars

echo "===> for set vars"

export DOMAIN="example.com"
export PREFIX="ai"
export HOSTNAME="${PREFIX}.${DOMAIN}"
echo DOMAIN: ${DOMAIN}
echo PREFIX: ${PREFIX}
echo HOSTNAME: ${HOSTNAME}

export PROJ_SLUG="foo"
export REGION="us-central1"
export MREGION="us"
echo PROJ_SLUG: ${PROJ_SLUG}
echo REGION: ${REGION}
echo MREGION: ${MREGION}

export VPC_VM="vm-${PROJ_SLUG}"
export ZONE="${REGION}-c"
echo VPC_VM: ${VPC_VM}
echo ZONE: ${ZONE}

export AGW_NAME="agw-${PROJ_SLUG}-${REGION}-ata"
echo AGW_NAME: ${AGW_NAME}

export GE_LOCATION="global"
export GE_APP_NAME="app-${PROJ_SLUG}-${GE_LOCATION}"
echo GE_LOCATION: ${GE_LOCATION}
echo GE_APP_NAME: ${GE_APP_NAME}


echo "===> for fetched vars"

export DOMAIN_RESOURCE="${DOMAIN//./-}"
echo DOMAIN_RESOURCE: ${DOMAIN_RESOURCE}

export AGENT_SLUG="decode"
export AGENT_NAME=agent-${AGENT_SLUG}
export AGENT_A2A_URL="https://${HOSTNAME}/${AGENT_NAME}"
echo AGENT_SLUG: ${AGENT_SLUG}
echo AGENT_NAME: ${AGENT_NAME}
echo AGENT_A2A_URL: ${AGENT_A2A_URL}

export MCP_SLUG="math"
export MCP_NAME="mcp-${MCP_SLUG}"
export MCP_URL="https://${MCP_NAME}-${PROJ_NO}.${REGION}.run.app/mcp"
echo MCP_SLUG: ${MCP_SLUG}
echo MCP_NAME: ${MCP_NAME}
echo MCP_URL: ${MCP_URL}

export PROJ_ID=$(gcloud config list --format="value(core.project)")
export PROJ_NO=$(gcloud projects describe ${PROJ_ID} --format="value(projectNumber)")
export ORG_ID=$(gcloud projects get-ancestors ${PROJ_ID} --format="value(id)" | tail -n 1)
echo PROJ_ID: ${PROJ_ID}
echo PROJ_NO: ${PROJ_NO}
echo ORG_ID: ${ORG_ID}

export AGW_URI="projects/${PROJ_ID}/locations/${REGION}/agentGateways/${AGW_NAME}"
echo AGW_URI: ${AGW_URI}

export USER_EMAIL=$(gcloud config get-value account)
echo USER_EMAIL: ${USER_EMAIL}
