#!/bin/sh

if [ -z "$CONFIG_MAP_NAME" -o -z "$APISERVER" -o -z "$APP_CONFIG_PATH" -o -z "$WES_APP_NAME" ];
then
	echo "CONFIG_MAP_NAME, APISERVER, APP_CONFIG_PATH, and WES_APP_NAME env vars required"
	env
	exit 1
fi
echo "Inputs:"
echo " CONFIG MAP NAME: $CONFIG_MAP_NAME"
echo " API SERVER:      $APISERVER"
echo " APP CONFIG PATH: $APP_CONFIG_PATH"
echo " WES APP NAME:    $WES_APP_NAME"

NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
echo "Current Kubernetes namespace: $NAMESPACE"; echo

echo " * Getting current default configuration"

APP_CONFIG=$(cat "$APP_CONFIG_PATH")

echo " * Getting current configMap"
curl -s \
  --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  -X GET \
  -H "Accept: application/json, */*" \
  -o /tmp/configmap.json \
  -w "Return HTTP/code: %{http_code}\n\n" \
"https://$APISERVER/api/v1/namespaces/${NAMESPACE}/configmaps/${CONFIG_MAP_NAME}"

echo " * Validating JSON file recevied:"; echo
jq . /tmp/configmap.json || exit 2

echo " JSON file is valid";echo

echo " * Creating update for secret"
jq ".data.\"app_config.yaml\" = \"$APP_CONFIG\"" /tmp/configmap.json >/tmp/configmap-patch.json

echo " * Validating JSON file patched:"; echo
jq . /tmp/configmap-patch.json || exit 3

echo " JSON file is valid";echo

# Update Config map
echo " * Updating config map"
curl -s \
  --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  -X PATCH \
  -H "Accept: application/json, */*" \
  -H "Content-Type: application/strategic-merge-patch+json" \
  -d @/tmp/configmap-patch.json "https://$APISERVER/api/v1/namespaces/${NAMESPACE}/configmaps/${CONFIG_MAP_NAME}" \
  -o /dev/null

echo " * Deleting current $WES_APP_NAME pod"
curl -s \
  --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  -X GET \
  -H "Accept: application/json, */*" \
  "https://$APISERVER/api/v1/namespaces/${NAMESPACE}/pods/" | \
jq '.items | .[] | .metadata.name ' -r | grep "^${WES_APP_NAME}-" | \
while read pod;
do
  echo "   - Deleting: $pod"
  curl -s \
    --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
    -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
    -X DELETE \
    -H "Accept: application/json, */*" \
    -o /dev/null \
    "https://$APISERVER/api/v1/namespaces/${NAMESPACE}/pods/$pod"
done

echo " All Done"

sleep 3600


