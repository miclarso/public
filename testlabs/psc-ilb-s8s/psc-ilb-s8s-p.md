---
lab: psc-ilb-s8s
---

# ilb psc neg to ilb s8s neg (producer)

![cartoon](img/psc-ilb-s8s.svg)

## setup

```sh
# set env vars
export PROJ_ID=$(gcloud config list --format="value(core.project)")
export PROJ_NO=$(gcloud projects describe $PROJ_ID --format="value(projectNumber)")
export ORG_ID=$(gcloud organizations list --format="value(name)")
export REGION_A="us-central1"
export ZONE_A="us-central1-f"
export REGION_B="us-east4"
export ZONE_B="us-east4-c"
export GCE_SA="${PROJ_NO}-compute@developer.gserviceaccount.com"
export USER_EMAIL=$(gcloud auth list --filter="status:ACTIVE" --format="value(account)")
export SLUG="phoenix"
export LOCAL_PATH="${HOME}/path/to/certs"
export CONSUMER_PROJ_NO="<CONSUMER_PROJECT_NUMBER>"
echo ${PROJ_ID}
echo ${PROJ_NO}
echo ${ORG_ID}
echo ${REGION_A}
echo ${ZONE_A}
echo ${REGION_B}
echo ${ZONE_B}
echo ${GCE_SA}
echo ${USER_EMAIL}
echo ${SLUG}
echo ${LOCAL_PATH}
echo ${CONSUMER_PROJ_NO}
```

```sh
# enable apis
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudresourcemanager.googleapis.com \
  certificatemanager.googleapis.com
```

## network

```sh
# create subnet for frontend
gcloud compute networks subnets create subnet-r1-1 \
  --range=10.71.1.0/24 \
  --network=vpc-z \
  --region=${REGION_A} \
  --enable-private-ip-google-access

gcloud compute networks subnets create subnet-r2-1 \
  --range=10.72.1.0/24 \
  --network=vpc-z \
  --region=${REGION_B} \
  --enable-private-ip-google-access


# create subnet for global proxy
gcloud compute networks subnets create subnet-r1-2 \
  --range=100.71.2.0/24 \
  --network=vpc-z \
  --region=${REGION_A} \
  --purpose=GLOBAL_MANAGED_PROXY \
  --role=ACTIVE

gcloud compute networks subnets create subnet-r2-2 \
  --range=100.72.2.0/24 \
  --network=vpc-z \
  --region=${REGION_B} \
  --purpose=GLOBAL_MANAGED_PROXY \
  --role=ACTIVE


# create subnet for psc nat
gcloud compute networks subnets create subnet-r1-3 \
  --range=100.71.3.0/24 \
  --network=vpc-z \
  --region=${REGION_A} \
  --purpose=PRIVATE_SERVICE_CONNECT

gcloud compute networks subnets create subnet-r2-3 \
  --range=100.72.3.0/24 \
  --network=vpc-z \
  --region=${REGION_B} \
  --purpose=PRIVATE_SERVICE_CONNECT


# create subnet for backend
gcloud compute networks subnets create subnet-r1-4 \
  --range=100.71.4.0/24 \
  --network=vpc-z \
  --region=${REGION_A} \
  --enable-private-ip-google-access

gcloud compute networks subnets create subnet-r2-4 \
  --range=100.72.4.0/24 \
  --network=vpc-z \
  --region=${REGION_B} \
  --enable-private-ip-google-access
```

## run

### iam

```sh
# give compute sa run builder role
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="serviceAccount:${GCE_SA}" \
  --role=roles/run.builder

# give compute sa run invoker role
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="serviceAccount:${GCE_SA}" \
  --role="roles/run.invoker"

# give user (self) run invoker role
gcloud projects add-iam-policy-binding ${PROJ_ID} \
  --member="user:${USER_EMAIL}" \
  --role="roles/run.invoker"
```

```sh
# give remote project (consumer) compute sa run invoker role on local project (producer)
gcloud projects add-iam-policy-binding ${PROJ_ID}\
  --member="serviceAccount:<consumer-project-number>-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### region 1

```sh
# create dir
mkdir helloworld-r1
```

```sh
# create main.py file
cat > helloworld-r1/main.py << EOF
import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name} from region 1!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
EOF
```

```sh
# create requirements.txt file
cat > helloworld-r1/requirements.txt << EOF
Flask==3.0.3
gunicorn==23.0.0
Werkzeug==3.0.3
EOF
```

```sh
# deploy run
gcloud -q run deploy helloworld-r1 \
  --source=./helloworld-r1 \
  --ingress=internal \
  --no-allow-unauthenticated \
  --add-custom-audiences="https://${SLUG}.your.domain.com" \
  --region=${REGION_A}
```

### region 2

```sh
# create dir
mkdir helloworld-r2
```

```sh
# create main.py file
cat > helloworld-r2/main.py << EOF
import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name} from region 2!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
EOF
```

```sh
# create requirements.txt file
cat > helloworld-r2/requirements.txt << EOF
Flask==3.0.3
gunicorn==23.0.0
Werkzeug==3.0.3
EOF
```

```sh
# deploy run
gcloud -q run deploy helloworld-r2 \
  --source=./helloworld-r2 \
  --ingress=internal \
  --no-allow-unauthenticated \
  --add-custom-audiences="https://${SLUG}.your.domain.com" \
  --region=${REGION_B}
```

### test

```sh
# ssh to vm
gcloud compute ssh vm-test --zone=${ZONE_A}
```

https://helloworld-r1-${PROJ_NO}.us-central1.run.app
https://helloworld-r2-${PROJ_NO}.us-east4.run.app

```sh
# get access token
export TOKEN=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=https://helloworld-r1-${PROJ_NO}.us-central1.run.app" -H "Metadata-Flavor: Google")

# make authenticated call
curl -H "Authorization: Bearer $TOKEN" https://helloworld-r1-${PROJ_NO}.us-central1.run.app
```

```sh
# get access token
export TOKEN=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=https://helloworld-r2-${PROJ_NO}.us-east4.run.app" -H "Metadata-Flavor: Google")

# make authenticated call
curl -H "Authorization: Bearer $TOKEN" https://helloworld-r2-${PROJ_NO}.us-east4.run.app
```

## load balancer

### certs

```sh
# upload certs to cert man
gcloud certificate-manager certificates create cert-priv-${SLUG} \
  --certificate-file="${LOCAL_PATH}/as-${SLUG}-cert.pem" \
  --private-key-file="${LOCAL_PATH}/as-${SLUG}-key.pem" \
  --scope=all-regions
```

### gilb

```sh
# create serverless neg
gcloud compute network-endpoint-groups create s8s-neg-z3-r1 \
  --region=${REGION_A} \
  --network-endpoint-type=serverless  \
  --cloud-run-service=helloworld-r1

gcloud compute network-endpoint-groups create s8s-neg-z3-r2 \
  --region=${REGION_B} \
  --network-endpoint-type=serverless  \
  --cloud-run-service=helloworld-r2
```

```sh
# create backend service
gcloud compute backend-services create bes-z3 \
  --load-balancing-scheme=INTERNAL_MANAGED \
  --protocol=HTTP \
  --global
```

```sh
# add negs groups to backend service
gcloud compute backend-services add-backend bes-z3 \
  --network-endpoint-group=s8s-neg-z3-r1 \
  --network-endpoint-group-region=${REGION_A} \
  --global

gcloud compute backend-services add-backend bes-z3 \
  --network-endpoint-group=s8s-neg-z3-r2 \
  --network-endpoint-group-region=${REGION_B} \
  --global
```

```sh
# create url map
gcloud compute url-maps create l7-gilb-z3 \
  --default-service=bes-z3 \
  --global
```

```sh
# create https proxy with cert
gcloud compute target-https-proxies create proxy-l7-gilb-z3 \
  --url-map=l7-gilb-z3 \
  --certificate-manager-certificates=cert-priv-${SLUG} \
  --global
```

```sh
# create forwarding rule
gcloud compute forwarding-rules create fr-l7-gilb-z3-r1 \
  --load-balancing-scheme=INTERNAL_MANAGED \
  --network=vpc-z \
  --subnet=subnet-r1-1 \
  --subnet-region=${REGION_A} \
  --address=10.71.1.88 \
  --ports=443 \
  --target-https-proxy=proxy-l7-gilb-z3 \
  --global

gcloud compute forwarding-rules create fr-l7-gilb-z3-r2 \
  --load-balancing-scheme=INTERNAL_MANAGED \
  --network=vpc-z \
  --subnet=subnet-r2-1 \
  --subnet-region=${REGION_B} \
  --address=10.72.1.88 \
  --ports=443 \
  --target-https-proxy=proxy-l7-gilb-z3 \
  --global
```

### dns

```sh
# create zone
gcloud dns managed-zones create priv-zone-name \
  --description=internal \
  --dns-name=your.domain.com \
  --networks=vpc-z \
  --visibility=private
```

```sh
# create record
gcloud dns record-sets create ${SLUG}.your.domain.com \
  --ttl="30" \
  --type="A" \
  --zone="priv-zone-name" \
  --routing-policy-type="GEO" \
  --enable-health-checking \
  --routing-policy-item=location=us-central1,internal_load_balancers=fr-l7-gilb-z3-r1@global \
  --routing-policy-item=location=us-east4,internal_load_balancers=fr-l7-gilb-z3-r2@global
```

### test


```sh
# ssh to vm
gcloud compute ssh vm-test --zone=${ZONE_A}
```

```sh
# Get access token with the custom audience
export TOKEN=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=https://${SLUG}.your.domain.com" -H "Metadata-Flavor: Google")

# make authenticated call
curl -k -H "Authorization: Bearer $TOKEN" https://${SLUG}.your.domain.com
```

### psc

```sh
# create service attachment
gcloud compute service-attachments create psc-sa-z3-r1 \
  --region=${REGION_A} \
  --target-service=projects/${PROJ_ID}/global/forwardingRules/fr-l7-gilb-z3-r1 \
  --connection-preference=ACCEPT_AUTOMATIC \
  --nat-subnets=subnet-r1-3

gcloud compute service-attachments create psc-sa-z3-r2 \
  --region=${REGION_B} \
  --target-service=projects/${PROJ_ID}/global/forwardingRules/fr-l7-gilb-z3-r2 \
  --connection-preference=ACCEPT_AUTOMATIC \
  --nat-subnets=subnet-r2-3
```

## cleanup

```sh
# delete 
gcloud -q run services delete helloworld-r1 --region=${REGION_A}
gcloud -q run services delete helloworld-r2 --region=${REGION_B}

gcloud -q artifacts docker images delete ${REGION_A}-docker.pkg.dev/${PROJ_ID}/cloud-run-source-deploy/helloworld-r1
gcloud -q artifacts docker images delete ${REGION_B}-docker.pkg.dev/${PROJ_ID}/cloud-run-source-deploy/helloworld-r2

gcloud -q projects remove-iam-policy-binding ${PROJ_ID} \
  --member="serviceAccount:${GCE_SA}" \
  --role=roles/run.builder

gcloud -q projects remove-iam-policy-binding ${PROJ_ID} \
  --member="serviceAccount:${GCE_SA}" \
  --role="roles/run.invoker"

gcloud -q projects remove-iam-policy-binding ${PROJ_ID} \
  --member="user:${USER_EMAIL}" \
  --role="roles/run.invoker"

gcloud -q projects remove-iam-policy-binding ${PROJ_ID} \
  --member="serviceAccount:${CONSUMER_PROJ_NO}-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"

# next
```

```sh
# delete
gcloud -q dns record-sets delete ${SLUG}.your.domain.com --type="A" --zone="priv-zone-name"

gcloud -q dns managed-zones delete priv-zone-name

gcloud -q compute service-attachments delete psc-sa-z3-r2 --region=${REGION_B}

gcloud -q compute service-attachments delete psc-sa-z3-r1 --region=${REGION_A}

gcloud -q compute forwarding-rules delete fr-l7-gilb-z3-r2 --global

gcloud -q compute forwarding-rules delete fr-l7-gilb-z3-r1 --global

gcloud -q compute target-https-proxies delete proxy-l7-gilb-z3 --global

gcloud -q compute url-maps delete l7-gilb-z3 --global

gcloud -q compute backend-services delete bes-z3 --global

gcloud -q compute network-endpoint-groups delete s8s-neg-z3-r2 --region=${REGION_B}

gcloud -q compute network-endpoint-groups delete s8s-neg-z3-r1 --region=${REGION_A}

gcloud -q certificate-manager certificates delete cert-priv-${SLUG} 

gcloud -q compute networks subnets delete subnet-r2-4 --region=${REGION_B}

gcloud -q compute networks subnets delete subnet-r1-4 --region=${REGION_A}

gcloud -q compute networks subnets delete subnet-r2-3 --region=${REGION_B}

gcloud -q compute networks subnets delete subnet-r1-3 --region=${REGION_A}

gcloud -q compute networks subnets delete subnet-r2-2 --region=${REGION_B}

gcloud -q compute networks subnets delete subnet-r1-2 --region=${REGION_A}

gcloud -q compute networks subnets delete subnet-r2-1 --region=${REGION_B}

gcloud -q compute networks subnets delete subnet-r1-1 --region=${REGION_A}

# end
```
