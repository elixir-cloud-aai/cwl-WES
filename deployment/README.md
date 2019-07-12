# Kubernetes deployment for WES

- [Kubernetes deployment for WES](#kubernetes-deployment-for-wes)
    - [Usage](#usage)
        - [Updates](#updates)
        - [Using with an external MongoDB](#using-with-an-external-mongodb)
        - [Setting up RabbitMQ for testing on OpenShift](#setting-up-rabbitmq-for-testing-on-openshift)
    - [Technical details](#technical-details)
        - [MongoDB](#mongodb)
        - [RabbitMQ](#rabbitmq)
        - [WES](#wes)

The files under this directory can be used to deploy WES on Kubernetes. The
directory structure is as follows:

- common: YAML files used in all Kubernetes clusters where this is deployed
  - mongodb: YAML for deploying MongoDB (TODO)
  - rabbitmq: YAML for deploying RabbitMQ (TODO)
  - wes: YAML for deploying WES Flask server and WES Celery worker
- ingress: cluster specific config for ingress (e.g. OpenShift Route or NGINX ingress)

## Usage

First you must create a namespace in Kubernetes in which to deploy WES. The
commands below assume that everything is created in the context of this
namespace. How the namespace is created depends on the cluster, so we won't
document it here.

There are some prerequisites to deploying WES on Kubernetes. Namely:

- MongoDB:
  - in the same namespace reachable via 'mongodb'
  - DB called wes-elixir-db created
  - database-user and database-password for wes-elixir-db available in a Secret
    called 'mongodb'
- RabbitMQ:
  - in the same namespace reachable via 'rabbitmq-cluster'
- Secret called netrc created (see below)

You'll need to configure an SFTP server connection using a .netrc file with the
following format:

```
machine my-sftp-server.com
login <username>
password <password>
```

Create a Kubernetes Secret from the .netrc file:

```bash
kubectl create secret generic netrc --from-file .netrc
```

After this you can deploy WES using kubectl:

```bash
cd deployment/common/wes
ls wes-* | xargs -L1 kubectl create -f
```

Once WES is deployed, you can expose it with the YAML files found under
`deployment/ingress`. Which file to use depnds on your cluster and how ingress
is configured there.

Creating an OpenShift Route:

```bash
cd deployment/ingress
oc create -f wes-route.yaml
```

### Updates

If you make changes to any of the Deployments, you can update them with
`kubectl`. For example, this is how you would update the Celery worker Deployment:

```bash
kubectl replace -f wes-celery-deployment.yaml
```

The OpenShift specific objects need to be updated using the `oc` tool instead.
Also, if you update the Route you must use the `--force` flag. This removes and
recreates the Route.

If you want to point to a different FTP server or change the login credentials
for the current FTP server, you can update the netrc secret like so:

```bash
kubectl create secret generic netrc --from-file .netrc --dry-run -o yaml | kubectl apply -f -
```

If you want to update the configuration, you can update the ConfigMap or use a
different ConfigMap with the same name. The Deployments expect to find the
`app_config.yaml` ConfigMap with the name `wes-config`. You can update the
ConfigMap like so:

```bash
kubectl replace -f wes-configmap.yaml
```

### Using with an external MongoDB

In certain situations, you may want to run an external MongoDB. There is an
example headless service file for this case under `deployment/mongodb`.

Make a copy of the example Service:

```bash
cd deployment/mongodb
cp mongodb-service-external.yaml.example mongodb-service-external.yaml
```

Edit the `mongodb-service-external.yaml` file and under `externalName` add your
external MongoDB's hostname. After this, create the Service:

```bash
kubectl create -f mongodb-service-external.yaml
```

It is assumed that the external MongoDB already has a database called
`wes-elixir-db` created and a user with read-write access available. Next you
will need to configure the MongoDB user and password in a secret (replace
`<username>` and `<password>`):

```bash
kubectl create secret generic mongodb --from-literal=database-user=<username> --from-literal=database-password=<password>
```

Depending on your MongoDB provider, the port may differ from 27017. In this
case, you will need to modify the Deployment files accordingly to use the
correct port (replace `<my external mongodb port>`):

```bash
cd deployment/common
find . -name *.yaml | xargs -L1 sed -i -e 's/27017/<my external mongodb port>/g'
```

After this you can deploy WES (see above).

### Setting up RabbitMQ for testing on OpenShift

During development of the WES deployment, a RabbitMQ cluster template was used
for testing integration with RabbitMQ in the same namespace:

[jharting/openshift-rabbitmq-cluster](https://github.com/jharting/openshift-rabbitmq-cluster)

The disadvantage with this template is that it only works with OpenShift because
it uses objects that are only available in OpenShift. For plain Kubernetes a
different approach needs to be used.

## Technical details

### MongoDB

TODO

### RabbitMQ

TODO

### WES

WES consists of two deployments: a Flask server and a Celery worker. These are
deployed using:

- wes-flask-deployment.yaml
- wes-celery-deployment.yaml

These deployments depend on setting up a shared ReadWriteMany volume between
Flask and Celery (`wes-volume.yaml`) and a shared ConfigMap
(`wes-configmap.yaml`).
