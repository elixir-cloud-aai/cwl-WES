#!/bin/sh
#
# Script to create a configMap using the default YAML file for the
# code.
#
####################################################################

APP_CONFIG="$1"
#
CONFIG_MAP='deployment/templates/wes/app-config.json'

#
# See if we have the tool to manipulate JSON
#
command -v jq >/dev/null || {
  echo;echo "ERROR: Command jq command not found. Please install it, or edit the configmap 'app-config' manualy with the changes you want to apply to app_config.yaml." >&2;
  exit 2
}
#

#
# See if we have the tool to interact with the cluster
#
if command -v kubectl >/dev/null
then
  KUBECTL='kubectl'
elif command -v oc >/dev/null
then
  KUBECTL='oc'
else
  echo;echo "ERROR: 'kubectl' nor 'oc' cannot be found. Please install any of them." >&2;
  exit 3
fi
#

#
# See if the default configuration file exists
#
if [ -z "$APP_CONFIG" ];
then
  APP_CONFIG=cwl_wes/config/app_config.yaml
fi

if [ ! -f "$APP_CONFIG" -o ! -f "$CONFIG_MAP" ];
then
  test -f "$APP_CONFIG" || echo "App config file '$APP_CONFIG', not found." >&2
  test -f "$CONFIG_MAP" || echo "Config ma definition '$CONFIG_MAP', not found." >&2
  echo "Use: $0 <APP_CONFIG> [CONFIG_MAP_DEFINITION]" >&2
  exit 1
fi
#


jq ".data.\"app_config.yaml\" = \"$(cat $APP_CONFIG)\"" $CONFIG_MAP | $KUBECTL replace --force -f -

