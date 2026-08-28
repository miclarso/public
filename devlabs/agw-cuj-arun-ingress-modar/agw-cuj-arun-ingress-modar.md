---
id: agw-cuj-arun-ingress-modar
---

# Agent Gateway ingress from Agent Runtime with Model Armor

## Codebase

The agent code and file data used for this Codelab are maintained in a remote
[Google Cloud GitHub repository][07-01]. The following steps will clone the
repository locally, copy the necessary files to the current working directory
structure, and then cleanup temporary files.

#### Fetch remote artifacts

```bash
# clone remote repository to temp local dir
git clone https://github.com/miclarso/public.git ./temp_agw_cuj_arun_ingress_modar
```

```bash
# copy agent runtime and endpoint definitions to working project dir
cp -r temp_agw_cuj_arun_ingress_modar/devlabs/agw-cuj-arun-ingress-modar/agent-crm ./agent-crm
```

```bash
# remove temporary directory
rm -rf temp_agw_cuj_arun_ingress_modar
```

[07-01]: https://github.com/miclarso/public/tree/main
