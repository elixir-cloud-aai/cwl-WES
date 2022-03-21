# Deployment instructions for Kubernetes

Installation via a Helm chart and configuration to deploy the WES service as well as MongoDB, Celery, RabbitMQ,
Flower and Autocert. This was tested with Helm v3.0.0.

## Prerequisites
1. A working kubernetes cluster and access to the ```kubectl``` command.
2. A dynamic storage provisioner ([StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)) that can provide volumes in ReadWriteMany (RWM) access mode. You can find [a list of internal provisioners](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes) that support this. We deployed cwl-WES successfully with an [external NFS volume provisioner](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs).
3. If you are planning to use cwl-WES in FTP mode you need an FTP server that supports TLS encryption. Choose from options:
    1. Use system wide certificate manager, see [Jetstack](https://hub.helm.sh/charts/jetstack/cert-manager) for install. Instance of ClusterIssuer is needed, YAML could look like:
        ```yaml
        apiVersion: cert-manager.io/v1alpha2
        kind: ClusterIssuer
        metadata:
          name: [name]
          labels:
            name: [name]
        spec:
          acme:
            email: email@example.com
            privateKeySecretRef:
              name: [name]
            server: https://acme-v02.api.letsencrypt.org/directory
            solvers:
            - http01:
                ingress:
                  class: nginx
        ```
        Also you need system wide ingress and load balancer configuration, see [Rancher Nginx](https://rancher.com/docs/rancher/v2.x/en/installation/options/nginx/) and [K8S RKE](https://rancher.com/docs/rancher/v2.x/en/installation/k8s-install/kubernetes-rke/).
        If you choose this option, in `values.yaml` set `autocert.createJob: "false"` and `ingress.letsencryptSystem: "true"`
    2. Install ingress and autocert from WES (set `autocert.createJob: "true"` and `ingress.letsencryptSystem: "false"`). For Autocert, see section below.
4. A working TES installation like [TESK](https://github.com/EMBL-EBI-TSI/TESK) or [Funnel](https://github.com/ohsu-comp-bio/funnel) exposed via an endpoint. If you are planning to use cwl-WES in FTP mode, then your TES endpoint must also support FTP.

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
		2. ```tesk.url```: The endpoint of your TES Service.
4. Navigate into the **[`deployment/`](/deployment) directory** and issue the following command:
```bash
helm install <name-of-your-deployment> . -f values.yaml -n <new-namespace-name>
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

## Security context
Many clusters feature security policy that forbids various actions in cluster. Usually, security policy includes requirement that resources must be deployed under non-root user. The requirement is satisfied by setting `securityContext` section in resources. 

`Values.yaml` offer setting security context only for Kubernetes clusters. It is set on two places:
- `mongodb.initContainer.runAsRoot` for settings related to mongoDB init container
- `mongodb.securityContext` for settings related to mongoDB
- `securityContext` for all other resources supporting security context

If you wish to run all your deployments under root, leave `securityContext`, set `mongodb.securityContext.runAsUser` to `0`, `mongodb.securityContext.runAsNonRoot` to `false` and `mongodb.initContainer.runAsRoot` to `true`. 

[MongoDB deployment](https://github.com/elixir-cloud-aai/cwl-WES/blob/dev/deployment/templates/mongodb/mongodb-deployment.yaml#L17) includes init container that runs only as root. If you can't run deployments under root, you should set `securityContext` and `mongodb.securityContext` sections to your needs and `mongodb.initContainer.runAsRoot` to `false` (leads to disabling root initContainer). `securityContext` is map of key value pairs that are directly translated to Kubernetes security context so you can set all key-value pairs allowed in the section, e.g.:
```
securityContext:                                                                
  runAsUser: 1000
  runAsNonRoot: true
  fsGroup: 1001
```

If you don't want to run under root but there you are not forced to run non-root, you can set security contexts as you wish where e.g. the `securityContext` and  `mongodb.securityContext` will be set to non-root and `mongodb.initContainer.runAsRoot` to `true` to keep the init container (chown can be done only under root user). 

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
| celeryWorker.image | string | container image to be used for the Celery application |
| clusterType | string | type of Kubernetes cluster; either 'kubernetes' or 'openshift' |
| ingress.letsencryptSystem | string | for K8S, whether use system LetsEncrypt or not |
| ingress.nginx_image | string | for K8S, container image to be used to run nginx |
| ingress.scope.annotations.clusterissuer | string | for K8S, name of instance of letsencrypt cert manager |
| ingress.scope.annotations.ingressclass | string | for K8S, name of class that takes care of ingress |
| ingress.scope.annotations.tlsacme | string | for K8S, true if letsencrypt should be used |
| mongodb.appName | string | name of MongoDB app on Kubernetes cluster |
| mongodb.databaseAdminPassword | string | admin password for MongoDB |
| mongodb.databaseName | string | name of MongoDB database to be used in application |
| mongodb.databasePassword | string | user password for MongoDB |
| mongodb.databaseUser | string | username for MongoDB |
| mongodb.image | string | container image to be used to run MongoDB |
| mongodb.initContainer.runAsRoot | bool | whether run init container under root user, see section `Security Context` for more information |
| mongodb.mountPath| string | for K8S, where to mount the PVC |
| mongodb.pullPolicy | string | pull Policy for container image |
| mongodb.securityContext.enabled | string | for K8S, whether security is enabled (to solve issues with newly created PVC) |
| mongodb.securityContext.fsGroup  | string | for K8S, fsGroup that can access the PVC |
| mongodb.securityContext.runAsUser  | string | for K8S, user that can access the PVC |
| mongodb.securityContext.runAsNonRoot  | string | for K8S, run as non root |
| mongodb.volumeSize | string | size of volume reserved for MongoDB database |
| rabbitmq.appName | string | name of RabbitMQ app on Kubernetes cluster |
| rabbitmq.image | string | container image to be used to run RabbitMQ |
| rabbitmq.volumeSize | string | size of volume reserved for RabbitMQ broker |
| securityContext | map | for K8s, if uncommented the whole section is translated into Kubernetes `securityContext`, see section `Security Context` |
| storageAccessMode | string | access mode for MongoDB and RabbitMQ PVC |
| tlsSecret | string | secret for TLS encryption |
| wes.appName | string | name of the main application on Kubernetes cluster |
| wes.image | string | containger image to be used for the main application |
| wes.netrcLogin | string | login name for accessing the sFTP server |
| wes.netrcMachine | string | host name of sFTP server |
| wes.netrcPassword | string | password for accessing the sFTP server |
| wes.storageClass | string | type of storageClass for WES, must have RWX capability |
| wes.volumeSize | string | size of volume reserved for the main application |
| wes.redirect | boolean | Activate/deactivate the '/' to '/ga4gh/wes/v1/ui/' redirection |
