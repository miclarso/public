---
id: agw-cuj-arun-egress-vpc
---

# Agent Gateway egress from Agent Runtime to VPC network

## Codebase
Duration: 10:00

The agent and MCP server code used for this
Codelab are maintained in a remote [GitHub repository][07-01]. The
following steps will clone the repository locally, copy the necessary files to
the current working directory structure, and then cleanup temporary files.

A storage staging bucket is created for Agent Runtime to upload, build, and
deploy the packaged agent application code and its dependency artifacts.

#### Fetch remote artifacts

```bash
# clone remote repository to temp local dir
git clone https://github.com/miclarso/public.git ./temp_agw_cuj_arun_egress_vpc
```

```bash
# copy agent runtime and endpoint definitions to working project dir
cp -r temp_agw_cuj_arun_egress_vpc/devlabs/agw-cuj-arun-egress-vpc/agent-weather ./agent-weather
cp -r temp_agw_cuj_arun_egress_vpc/devlabs/agw-cuj-arun-egress-vpc/mcp-weather ./mcp-weather
```

```bash
# remove temporary directory
rm -rf temp_agw_cuj_arun_egress_vpc
```

#### Create staging bucket

```bash
# create storage bucket for agent deployment artifacts
gcloud storage buckets create gs://${STAGING_BUCKET} --location=${REGION}
```

```bash
# verify staging bucket url
gcloud storage buckets list --format="value(storage_url)"
```

This concludes the codebase portion... next on to the *Registry* section.

[07-01]: https://github.com/miclarso/public/tree/main
