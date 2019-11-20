wes
===
A workflow execution service (WES) WES-ELIXIR helm chart

Current chart version is `0.1.0`





## Chart Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| applicationDomain | string | `"c03.k8s-popup.csc.fi"` |  |
| autocert.apiServer | string | `"kubernetes.default.svc:443"` | where to reach k8s apiserver |
| autocert.createJob | string | `"true"` | Actually create autocert cronjob |
| autocert.email | string | `"cert.author@cert.author.host.org"` | which email to inject to the certificate |
| autocert.image | string | `"elixircloud/autocert:devel"` |  |
| autocert.schedule | string | `"0 0 1 */2 *"` | How often to refresh certs |
| autocert.testCert | string | `"true"` | use letsencryptit staging for testing not to exceed cert quota |
| celeryWorker.appName | string | `"celery-worker-wes"` |  |
| celeryWorker.image | string | `"weselixir/elixir-wes-app:rc1"` |  |
| clusterType | string | `"openshift"` |  |
| mongodb.appName | string | `"mongodb"` |  |
| mongodb.databaseAdminPassword | string | `"adminpasswd"` |  |
| mongodb.databaseName | string | `"wes-elixir-db"` |  |
| mongodb.databasePassword | string | `"protes-db-passwd"` |  |
| mongodb.databaseUser | string | `"protes-user"` |  |
| mongodb.image | string | `"centos/mongodb-36-centos7"` |  |
| mongodb.volumeSize | string | `"1Gi"` | Size for mongodb database |
| rabbitmq.appName | string | `"rabbitmq"` |  |
| rabbitmq.image | string | `"rabbitmq:3-management"` |  |
| rabbitmq.volumeSize | string | `"1Gi"` | Size for mongodb database |
| tlsSecret | string | `"mytls-secret"` |  |
| wes.appName | string | `"wes"` | name of the application in k8s cluster |
| wes.image | string | `"weselixir/elixir-wes-app:rc1"` | which image if WES to use |
| wes.netrcLogin | string | `"defaultnetrclogin"` |  |
| wes.netrcMachine | string | `"defaultmachine"` | SFTP machine adddress |
| wes.netrcPassword | string | `"defaultnetrcpassword"` |  |
| wes.volumeSize | string | `"1Gi"` | Size of the PVC volume for WES |
