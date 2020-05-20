# Deployment instructions

Helm chart and config to deploy the WES service, MongoDB, Celery, RabbitMQ,
Flower and Autocert. Tested with Helm v3.0.0.

## Usage

First you must create a namespace in Kubernetes in which to deploy WES. The
command below creates all deployments in the context of this namespace. How
the namespace is created depends on the cluster, so it is not documented here.

To deploy the application, first modify [`values.yaml`](values.yaml) or provide
an external value file, then execute:

```bash
helm install <deployment-name> . -f <values-yaml>
```

## Change application configuration

This helm chart will automatically create a config map called [app-config](/deployment/templates/wes/app-config.json). This is created using a `Job` that upon creation will run once and copy the default configuration file [app_config.yaml](/cwl_wes/config/app_config.yaml) into the aforementioned config map.

After changing the configuration, the pod running cwlwes must be reloded.

## Autocert

The helm chart utilizes scheduled TLS certificate fetching from [Let's
Encrypt](https://letsencrypt.org/).

## To do

- Test autocert with vanilla Kubernetes

## Description of values

See [`values.yaml`](values.yaml) for default values.

| Key | Type | Description |
| --- | --- | --- |
| applicationDomain | string | where to reach the Kubernetes cluster |
| autocert.apiServer | string | where to reach the Kubernetes API server |
| autocert.createJob | string | create autocert cronjob |
| autocert.email | string | email to inject into the certificate |
| autocert.image | string | container image to be used to run Autocert |
| autocert.schedule | string | schedule for certificate refreshment |
| autocert.testCert | string | whether to use Let's Encrypt staging so as not to exceed quota |
| celeryWorker.appName | string | name of the Celery app on Kubernetes cluster |
| celeryWorker.image | string | containger image to be used for the Celery application |
| clusterType | string | type of Kubernetes cluster; either 'kubernetes' or 'openshift' |
| mongodb.appName | string | name of MongoDB app on Kubernetes cluster |
| mongodb.databaseAdminPassword | string | admin password for MongoDB |
| mongodb.databaseName | string | name of MongoDB database to be used in application |
| mongodb.databasePassword | string | user password for MongoDB |
| mongodb.databaseUser | string | username for MongoDB |
| mongodb.image | string | container image to be used to run MongoDB |
| mongodb.volumeSize | string | size of volume reserved for MongoDB database |
| rabbitmq.appName | string | name of RabbitMQ app on Kubernetes cluster |
| rabbitmq.image | string | container image to be used to run RabbitMQ |
| rabbitmq.volumeSize | string | size of volume reserved for RabbitMQ broker |
| tlsSecret | string | secret for TLS encryption |
| wes.appName | string | name of the main application on Kubernetes cluster |
| wes.image | string | containger image to be used for the main application |
| wes.netrcLogin | string | login name for accessing the sFTP server |
| wes.netrcMachine | string | host name of sFTP server |
| wes.netrcPassword | string | password for accessing the sFTP server |
| wes.volumeSize | string | size of volume reserved for the main application |

