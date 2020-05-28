# Deployment instructions for Kubernetes

Installation via a Helm chart and configuration to deploy the WES service as well as MongoDB, Celery, RabbitMQ,
Flower and Autocert. This was tested with Helm v3.0.0.

## Prerequisites
1. A working kubernetes cluster and access to the ```kubectl``` command.
2. A dynamic storage provisioner ([StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)) that can provide volumes in ReadWriteMany (RWX) access mode. You can find [a list of internal provisioners](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes) that support this. We deployed cwl-WES successfully with an [external NFS volume provisioner](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs).
3. If you are planning to use cwl-WES in FTP mode you need an FTP server that supports TLS encryption. 
4. A working TES installation like [TESK](https://github.com/EMBL-EBI-TSI/TESK) or Funnel(https://github.com/ohsu-comp-bio/funnel) exposed via an endpoint. If you are planning to use cwl-WES in FTP mode, then your TES endpoint must also support FTP.

## Deploying in FTP mode
1. Create a new namespace in Kubernetes in which to deploy WES:
```bash
kubectl create namespace <new-namespace-name>
```
2. Change the following values in [`values.yaml`](values.yaml) (for a detailed list of configuration values look further down):
	1. ```clusterType```: Set to "kubernetes".
	2. ```wes.netrcMachine```: the endpoint of your FTP service.
	3. ```wes.netrcLogin```: the username of your FTP service.
	4. ```wes.netrcPassword```: the password of your FTP service. 
	It is important that your FTP login and password do not contain any special characters used in URLs like (#,&,?,etc) because they can cause errors to be produced.
3. Change the application configuration:
	1. Change the following values in [/cwl_wes/config/app_config.yaml](/cwl_wes/config/app_config.yaml):
		1. ```storage.remote_storage_url```: The endpoint and folder of the FTP service that will be used for remote storage:
		```ftp://endpoint//path```
		2. ```tes.url```: The endpoint of your TES Service.
4. Navigate into the **[`deployment/`](/deployment) directory** and issue the following command:
```bash
helm install <name-of-your-deployment> . -f <values.yaml> -n <new-namespace-name>
```
Helm should provision volumes for Rabbitmq, MongoDB and cwl-WES:
```bash
kubectl -n <new-namespace-name> get pvc 
```
Moreover you should see 5 new pods created in the new namespace (they should all settle in Running status after a while):
```bash
kubectl -n <new-namespace-name> get pods
```

## Deploy in shared-volume mode.
TODO

## Test using the hashspitter workflow:
```bash
curl -X POST \
	 --header 'Content-Type: multipart/form-data' \
	 --header 'Accept: application/json' \
	 -F workflow_params='{"input":{"class":"File","path":"<add_a_path_to_a_file_here>"}}' \
	 -F workflow_type='CWL' \
	 -F workflow_type_version='v1.0'  \
	 -F workflow_url='https://github.com/uniqueg/cwl-example-workflows/blob/master/hashsplitter-workflow.cwl' \
	 '<wes_endpoint>/ga4gh/wes/v1/runs'
```

## Autocert

The helm chart utilizes scheduled TLS certificate fetching from [Let's
Encrypt](https://letsencrypt.org/).

## To do

- Test autocert with vanilla Kubernetes

## Description of values in [`values.yaml`](values.yaml)

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

