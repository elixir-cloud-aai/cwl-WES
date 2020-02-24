#!/bin/sh

if [[ -z $EMAIL || -z $DOMAINS || -z $SECRET || -z $APISERVER ]]; then
	echo "EMAIL, DOMAINS, SECRET, and APISERVER env vars required"
	env
	exit 1
fi
echo "Inputs:"
echo " EMAIL: $EMAIL"
echo " DOMAINS: $DOMAINS"
echo " SECRET: $SECRET"
echo " ROUTE: $ROUTE"


NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
echo "Current Kubernetes namespce: $NAMESPACE"

echo "Starting HTTP server... "
WEBROOT=/tmp/challenge
mkdir -p /tmp/challenge
(cd /tmp/challenge && python3 -m http.server 8080) &
PID=$(pidof python3)

echo "Wait a little so that service will see us"
sleep 20

# use staging
echo "Starting certbot..."
certbot certonly $TESTCERT --webroot -w $WEBROOT -n --agree-tos --email ${EMAIL} --no-self-upgrade -d ${DOMAINS} \
  --config-dir=/tmp/cfg --logs-dir=/tmp/log --work-dir=/tmp/work
kill $PID

echo "Certbot finished. Killing http server..."

echo "Finiding certs. Exiting if certs are not found ..."
CERTPATH=/tmp/cfg/live/$(echo $DOMAINS | cut -f1 -d',')
ls $CERTPATH || exit 1

echo "Creating update for secret..."
cat /secret-patch-template.json | \
	sed "s/NAMESPACE/${NAMESPACE}/" | \
	sed "s/NAME/${SECRET}/" | \
	sed "s/TLSCERT/$(cat ${CERTPATH}/fullchain.pem | base64 | tr -d '\n')/" | \
	sed "s/TLSKEY/$(cat ${CERTPATH}/privkey.pem |  base64 | tr -d '\n')/" \
	> /tmp/secret-patch.json

echo "Checking json file exists. Exiting if not found..."
ls /tmp/secret-patch.json || exit 1

# Update Secret
echo "Updating secret..."
curl \
  --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  -XPATCH \
  -H "Accept: application/json, */*" \
  -H "Content-Type: application/strategic-merge-patch+json" \
  -d @/tmp/secret-patch.json https://$APISERVER/api/v1/namespaces/${NAMESPACE}/secrets/${SECRET} \
  -k -v
echo "Done"

# Update route
if [[ -z $ROUTE ]]; then
  echo "Not creating route patch."
else
  cat ${CERTPATH}/fullchain.pem | tr '\n' % | sed 's@%@\\\\n@g' > /tmp/full.pem
  cat ${CERTPATH}/privkey.pem | tr '\n' % | sed 's@%@\\\\n@g' > /tmp/key.pem
  echo "Creating route patch"
  cat /route-patch-template.json | \
	sed "s/NAMESPACE/${NAMESPACE}/" | \
	sed "s/ROUTENAME/${ROUTE}/" | \
        sed "s@TLSCERT@$(cat /tmp/full.pem)@" | \
        sed "s@TLSKEY@$(cat /tmp/key.pem)@" \
	> /tmp/route-patch.json

  echo "Updating route..."
  curl \
    --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
    -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
    -XPATCH \
    -H "Accept: application/json, */*" \
    -H "Content-Type: application/strategic-merge-patch+json" \
    -d @/tmp/route-patch.json https://$APISERVER/apis/route.openshift.io/v1/namespaces/${NAMESPACE}/routes/${ROUTE} \
    -k -v
fi

