---
title: Looker PSC Southbound access to multiple Cloud SQL PSC instances through proxy
path: /cloudnet-psc-looker-cloudsql-southbound-proxy
slug: looker-psc-csql
---

# looker psc csql

## 4 prep steps

```sh
# set vars
export project_id=$(gcloud config list --format="value(core.project)")
export mylooker_project=${project_id}
export mylooker=$(gcloud looker instances list --region=$region --format="value(name)")
export region=us-central1
export zone=$region-b
echo $project_id
echo $mylooker_project
echo $mylooker
echo $region
echo $zone
```

```sh
# enable apis
gcloud services enable \
  compute.googleapis.com \
  dns.googleapis.com \
  networkconnectivity.googleapis.com \
  sqladmin.googleapis.com
```

```sh
# create vnet
gcloud compute networks create my-net \
  --subnet-mode=custom
```

```sh
# create subnets
gcloud compute networks subnets create my-subnet \
  --network=my-net \
  --range=10.10.0.0/24 \
  --region=$region

gcloud compute networks subnets create psc-subnet \
  --network=my-net \
  --region=$region \
  --range=192.168.0.0/28 \
  --purpose=PRIVATE_SERVICE_CONNECT
```

```sh
# create nat
gcloud compute routers create $region-cr \
  --network=my-net \
  --region=$region

gcloud compute routers nats create $region-nat \
  --router=$region-cr \
  --region=$region \
  --nat-all-subnet-ip-ranges \
  --auto-allocate-nat-external-ips
```

```sh
# create fw policy
gcloud compute network-firewall-policies create global-fw-policy --global

gcloud compute network-firewall-policies associations create \
  --firewall-policy=global-fw-policy \
  --name=producer-fw-policy \
  --network=my-net \
  --global-firewall-policy 
```

```sh
# create fw rules
gcloud compute network-firewall-policies rules create 100 \
  --action=ALLOW \
  --firewall-policy=global-fw-policy \
  --description="producer-allow-iap" \
  --direction=INGRESS \
  --src-ip-ranges=35.235.240.0/20 \
  --layer4-configs=tcp:22 \
  --global-firewall-policy

gcloud compute network-firewall-policies rules create 200 \
  --action=ALLOW \
  --firewall-policy=global-fw-policy \
  --description="producer-allow-access-service" \
  --direction=INGRESS \
  --src-ip-ranges=192.168.0.0/28 \
  --layer4-configs=tcp \
  --global-firewall-policy
```

## 5 cloud sql

```sh
# create psc service connection policy
gcloud network-connectivity service-connection-policies create allow-cloudsql-psc \
  --network=my-net \
  --project=$project_id \
  --region=$region \
  --service-class=google-cloud-sql \
  --subnets=https://www.googleapis.com/compute/v1/projects/$project_id/regions/$region/subnetworks/my-subnet \
  --psc-connection-limit=10 \
  --description="Cloud SQL service connection policy" \
  --producer-instance-location=custom-resource-hierarchy-levels \
  --allowed-google-producers-resource-hierarchy-level=projects/$project_id
```

```sh
# create csql instance
gcloud sql instances create mysql1 \
  --region=$region \
  --enable-private-service-connect \
  --allowed-psc-projects=$project_id \
  --availability-type=ZONAL \
  --no-assign-ip \
  --edition=enterprise \
  --cpu=2 \
  --memory=4GB \
  --database-version=MYSQL_8_0 \
  --root-password=password123 \
  --async
```

```sh
# patch csql instance for psc ep auto creation
gcloud sql instances patch mysql1 \
  --psc-auto-connections=network=projects/$project_id/global/networks/my-net,project=$project_id \
  --async
```

```sh
# create csql instance
gcloud sql instances create mysql2 \
  --region=$region \
  --enable-private-service-connect \
  --allowed-psc-projects=$project_id \
  --availability-type=ZONAL \
  --no-assign-ip \
  --edition=enterprise \
  --cpu=2 \
  --memory=4GB \
  --database-version=MYSQL_8_0 \
  --root-password=password123 \
  --async
```

```sh
# check state
gcloud sql instances describe mysql2 --format="value(state)"
```

```sh
# patch csql instance for psc ep auto creation
gcloud sql instances patch mysql2 \
  --psc-auto-connections=network=projects/$project_id/global/networks/my-net,project=$project_id \
  --async
```

```sh
# fetch psc ep ip addresses
mysql1_ip=$(gcloud sql instances describe mysql1 \
  --format='value(settings.ipConfiguration.pscConfig.pscAutoConnections.ipAddress)')

mysql2_ip=$(gcloud sql instances describe mysql2 \
  --format='value(settings.ipConfiguration.pscConfig.pscAutoConnections.ipAddress)')

echo $mysql1_ip
echo $mysql2_ip
```

## 6 dns

```sh
# create dns zone
gcloud dns managed-zones create test-com \
  --description="for database" \
  --dns-name=test.com \
  --networks=my-net \
  --visibility=private
```

```sh
# create dns records
gcloud dns record-sets create mysql1.test.com \
  --rrdatas=$mysql1_ip \
  --ttl=300 \
  --type=A \
  --zone=test-com

gcloud dns record-sets create mysql2.test.com \
  --rrdatas=$mysql2_ip \
  --ttl=300 \
  --type=A \
  --zone=test-com
```

## 7 nginx

```sh
# create vm
gcloud compute instances create my-nginx \
  --zone=$zone \
  --subnet=my-subnet \
  --shielded-secure-boot \
  --no-address
```

```sh
# ssh to vm
gcloud compute ssh "my-nginx" --zone=$zone
```

```sh
# install nginx
sudo apt update && sudo apt install nginx -y
sudo apt install libnginx-mod-stream -y
sudo nginx -V
```

```sh
# check for --with-stream
sudo nginx -V 2>&1 | grep -o 'with-stream[^ ]*'
```

```sh
# update nginx config file
sudo tee /etc/nginx/nginx.conf > /dev/null <<'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
error_log /var/log/nginx/error.log;
include /etc/nginx/modules-enabled/*.conf;

events {
        worker_connections 768;
}

http {
        sendfile on;
        tcp_nopush on;
        types_hash_max_size 2048;
        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE
        ssl_prefer_server_ciphers on;

        access_log /var/log/nginx/access.log;

        gzip on;

        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
}

stream {
        upstream database1 {
                server mysql1.test.com:3306;
        }       
        upstream database2 {
                server mysql2.test.com:3306;
        }

        server {
                listen 1000;
                proxy_connect_timeout 60s;
                proxy_socket_keepalive on;
                proxy_pass database1;
        }

        server {
                listen 1001;
                proxy_connect_timeout 60s;
                proxy_socket_keepalive on;
                proxy_pass database2;
        }
}
EOF
```

```sh
# test config syntax
sudo nginx -t
```

```sh
# restart nginx
sudo systemctl restart nginx
```

```sh
# exit vm
exit
```

## 8 publish service

```sh
# create neg (port-mapping type)
gcloud compute network-endpoint-groups create nginx-neg \
  --region=$region \
  --network=my-net \
  --subnet=my-subnet \
  --network-endpoint-type=GCE_VM_IP_PORTMAP
```

```sh
# add endpoints to neg
gcloud compute network-endpoint-groups update nginx-neg \
  --region=$region \
  --add-endpoint=client-destination-port=1000,instance=projects/$project_id/zones/$zone/instances/my-nginx,port=1000 \
  --add-endpoint=client-destination-port=1001,instance=projects/$project_id/zones/$zone/instances/my-nginx,port=1001
```

```sh
# create backend service
gcloud compute backend-services create nginx-service \
  --load-balancing-scheme=internal \
  --region=$region \
  --network=my-net
  
gcloud compute backend-services add-backend nginx-service \
  --network-endpoint-group=nginx-neg \
  --network-endpoint-group-region=$region
```

```sh
# reserve ip address
gcloud compute addresses create l4-ilb-ip-address \
  --region=$region \
  --subnet=my-subnet

# create forwarding rule
gcloud compute forwarding-rules create publish-nginx \
  --load-balancing-scheme=INTERNAL \
  --ip-protocol=TCP \
  --network=my-net \
  --subnet=my-subnet \
  --address=l4-ilb-ip-address \
  --ports=ALL \
  --region=$region \
  --backend-service=nginx-service
```

```sh
# fetch looker tenant project id
export LOOKER_TENANT_PROJECT=$(gcloud looker instances describe $mylooker --project=$mylooker_project --region=$region --format="value(pscConfig.lookerServiceAttachmentUri.segment(1))")
echo $LOOKER_TENANT_PROJECT
```

```sh
# publish psc service
gcloud compute service-attachments create nginx-psc-service \
  --region=$region \
  --target-service=projects/$project_id/regions/$region/forwardingRules/publish-nginx \
  --connection-preference=ACCEPT_MANUAL \
  --consumer-accept-list=${LOOKER_TENANT_PROJECT}=5 \
  --nat-subnets=psc-subnet
```

```sh
# fetch nginx psc sa uri
export nginx_service_attachment=$(gcloud compute service-attachments describe nginx-psc-service --region=$region --format="value(selfLink.scope(v1))")
echo $nginx_service_attachment
```

## 9 looker psc ep

```sh
# check if any existing service attachments
gcloud looker instances describe $mylooker --region=$region --format="value(pscConfig.serviceAttachments)"
```

```sh
# create looker psc ep
gcloud looker instances update $mylooker \
  --region=$region \
  --psc-service-attachment=multiple-domains="mysql1.test.com;mysql2.test.com",attachment=$nginx_service_attachment
```

> [!note]
> if existing service attachments, include existing (b/c its an overwrite command)
> ```sh
> # create looker psc ep (with existing service attachments)
> gcloud looker instances update $mylooker \
>   --region=$region \
>   --psc-service-attachment=multiple-domains="existing-domain1.com;existing-domain2.com",attachment=projects/existing-project/regions/us-central1/serviceAttachments/existing-sa \
>   --psc-service-attachment=multiple-domains="mysql1.test.com;mysql2.test.com",attachment=$nginx_service_attachment
> ```

```sh
# check psc sa status
gcloud looker instances describe $mylooker --region=$region --format=json --format="value(pscConfig.serviceAttachments)"
```

## 10 test

> all in looker console

## cleanup

```sh
# delete
gcloud compute instances delete my-nginx --zone $zone --quiet

gcloud looker instances update $mylooker --region=$region --clear-psc-service-attachments -q

# next
```

```sh
# delete
gcloud compute service-attachments delete nginx-psc-service --region=$region --quiet

gcloud compute forwarding-rules delete publish-nginx --region=$region --quiet

gcloud compute backend-services delete nginx-service --region=$region --quiet

gcloud compute network-endpoint-groups delete nginx-neg --region=$region --quiet

# next
```

```sh
# delete
gcloud sql instances delete mysql1 --quiet --async

gcloud sql instances delete mysql2 --quiet --async

# next
```

```sh
# delete
gcloud compute network-firewall-policies associations delete --firewall-policy=global-fw-policy \
  --name=producer-fw-policy --global-firewall-policy --quiet

gcloud compute network-firewall-policies delete global-fw-policy --global --quiet

gcloud compute routers nats delete $region-nat --router=$region-cr --region=$region --quiet

gcloud compute routers delete $region-cr --region=$region --quiet

gcloud compute addresses delete l4-ilb-ip-address --region=$region --quiet

gcloud compute networks subnets delete my-subnet --region=$region --quiet

gcloud compute networks subnets delete psc-subnet --region=$region --quiet

gcloud compute networks delete my-net --quiet

# end
```

# addendum

## psc lb logs

```sh
# enable lb logs
$ gcloud compute backend-services update nginx-service  --region=$region  --enable-logging
```

```sh
# show log balancer logs
gcloud logging read 'logName="projects/'"$project_id"'/logs/loadbalancing.googleapis.com%2Fflows"' \
  --limit=10 \
  --format="table(
    timestamp.date(tz=LOCAL):label=TIME,
    jsonPayload.connection.clientIp:label=LOOKER_PSC_IP,
    jsonPayload.connection.clientPort:label=LOOKER_PORT,
    jsonPayload.connection.serverIp:label=ILB_IP,
    jsonPayload.connection.serverPort:label=ILB_PORT
  )"
```

```log
TIME                 LOOKER_PSC_IP  LOOKER_PORT  ILB_IP     ILB_PORT
2026-06-11T13:33:25  192.168.0.2    1035         10.10.0.5  1001
2026-06-11T13:33:25  192.168.0.2    1034         10.10.0.5  1001
2026-06-11T13:33:25  192.168.0.2    1033         10.10.0.5  1001
2026-06-11T13:33:25  192.168.0.2    1030         10.10.0.5  1001
2026-06-11T13:33:25  192.168.0.2    1032         10.10.0.5  1001
2026-06-11T13:33:25  192.168.0.2    1031         10.10.0.5  1001
2026-06-11T13:33:23  192.168.0.2    1032         10.10.0.5  1000
2026-06-11T13:33:23  192.168.0.2    1035         10.10.0.5  1000
2026-06-11T13:33:23  192.168.0.2    1034         10.10.0.5  1000
2026-06-11T13:33:23  192.168.0.2    1033         10.10.0.5  1000
```