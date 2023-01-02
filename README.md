# cwl-WES

[![License][badge-license]][badge-url-license]
[![CI][badge-ci]][badge-url-ci]
[![Website][badge-health]][badge-url-health]

## Synopsis

Microservice implementing the [Global Alliance for Genomics and
Health][org-ga4gh] (GA4GH) [Workflow Execution Service][res-ga4gh-wes] (WES)
API specification for the execution of workflows written in the [Common
Workflow Language][res-cwl] (CWL).

cwl-WES is a core service of the [ELIXIR Cloud & AAI
project][org-elixir-cloud].

## Description

cwl-WES (formerly: WES-ELIXIR) is a [Flask][res-flask]/[Gunicorn][res-gunicorn]
application that makes use of [Connexion][res-connexion] to implement the
[GA4GH WES OpenAPI specification][res-ga4gh-wes]. It enables clients/users
to execute [CWL][res-cwl] workflows in the cloud via a [GA4GH Task Execution
Service][res-ga4gh-tes] (TES)-compatible execution backend (e.g.,
[TESK][res-tesk] or [Funnel][res-funnel]). Workflows can be sent for execution,
previous runs can be listed, and the status and run information of individual
runs can be queried. The service leverages [cwl-tes][res-cwl-tes] to
interpret [CWL][res-cwl] workflows, break them down into individual tasks and
emit [GA4GH TES][res-ga4gh-tes]-compatible HTTP requests to a configured
[TES][res-ga4gh-tes] instance. Access to endpoints can be configured to require
[JSON Web Token][res-jwt-rfc]-based access tokens, such as those issued by
[ELIXIR AAI][res-elixir-aai]. Run information is stored in a
[MongoDB][res-mongo] database.

Note that development is currently in beta stage. Check the website badge at
the top of this document for a publicly available test deployment. Further
test deployments can be found at the [ELIXIR Cloud & AAI's resource
listings][res-elixir-cloud-resources].

cwl-WES is developed and maintained by the [ELIXIR Cloud & AAI
project][org-elixir-cloud], a multinational effort aimed at establishing and
implementing [FAIR][res-fair] research in the Life Sciences.

## Installation

### Kubernetes

See separate instructions available [here][docs-kubernetes].

### docker-compose

#### Requirements

Ensure you have the following software installed:

* Docker (18.06.1-ce, build e68fc7a)
* docker-compose (1.22.0, build f46880fe)
* Git (1.8.3.1)

> These are the versions used for development/testing. Other versions may or
> may not work. Please let us know if you encounter any issues with _newer_
> versions than the listed ones.

#### Instructions

##### Set up environment

Create data directory and required subdiretories:

```bash
mkdir -p data/cwl_wes/db data/cwl_wes/output data/cwl_wes/tmp
```

Clone repository:

```bash
git clone https://github.com/elixir-cloud-aai/cwl-WES.git
```

Traverse to app directory:

```bash
cd app
```

##### Optional: Edit/override app config

* Via the **app configuration file**

  ```bash
  vi cwl_wes/config.yaml
  ```

* Via **environment variables**

  A few configuration settings can be overridden by environment variables:

  ```bash
  export <ENV_VAR_NAME>=<VALUE>
  ```

  List of the available environment variables:

  | Variable       | Description             |
  |----------------|-------------------------|
  | MONGO_HOST     | MongoDB host endpoint   |
  | MONGO_PORT     | MongoDB service port    |
  | MONGO_DBNAME   | MongoDB database name   |
  | MONGO_USERNAME | MongoDB client username |
  | MONGO_PASSWORD | MongoDB client password |
  | RABBIT_HOST    | RabbitMQ host endpoint  |
  | RABBIT_PORT    | RabbitMQ service port   |

###### Build & deploy

Build and run services in detached/daemonized mode:

```bash
docker-compose up -d --build
```

###### Copy FTP credentials

Create a `.netrc` file with credentials for accessing an FTP server:

```bash
cat << EOF > .netrc
machine <HOST>
login <USERNAME>
password <PASSWORD>
EOF
```

> Don't forget to replace `<HOST>`, `<USERNAME>` and `<PASSWORD>` with real
> values.
>
> If you do not know what to put here, creating an empty file `.netrc` with,
> e.g., `touch .netrc` will be fine for testing purposes.

Copy the file into the running worker container(s):

```bash
for cont in $(docker ps --all | grep wes-worker | cut -f1 -d" "); do
    docker cp .netrc "${cont}:/tmp/user"
done
```

###### Use service

Visit Swagger UI:

```bash
firefox http://localhost:8080/ga4gh/wes/v1/ui
```

Example values to start a simple CWL test workflow via the `POST /runs`
endpoint:

```console
workflow_params: {"input":{"class":"File","path":"ftp://ftp-private.ebi.ac.uk/upload/foivos/test.txt"}}`
workflow_type: CWL
workflow_type_version`: v1.0
workflow_url: https://github.com/uniqueg/cwl-example-workflows/blob/master/hashsplitter-workflow.cwl
```

Leave the rest of the values empty and hit the `Try it out!` button.

You can also use the service through `curl`. For example, to send a request to
the `GET /runs` endpoint:

```console
curl -X GET \
    --header 'Accept: application/json' \
    'http://localhost:8080/ga4gh/wes/v1/runs' 
```

###### Authorization

All endpoints except for `GET /service-info` can be configured to require the
presence of a valid JWT Bearer token in a request's header. This can be enabled
by setting the following paraneter in the [app configuration][config-app] to
`True`:

```yaml
# Security settings
security:
    authorization_required: True
```

To send authorized requests, you **must** be in possession of a valid JWT
Bearer token. The app was developed against JWTs issues by
[ELIXIR AAI][elixir-aai], although JWTs issued by other identity providers may
work.

If you want to utilize actual compute resources in any of the ELIXIR test
deployments, you **must** be a member of a specific ELIXIR user group. You can
apply [here][elixir-user-group-apply] to be added to that group (ELIXIR AAI
only!). When applying, please include a brief description of why you would like
to make use of our test deployments and please note that they are for fair use
only (please don't try to run your production workflows on them or we will need
to re-think our strategy of offering free resources for testing/developing).

To access protected endpoints via `curl`, you only need to add an `Authorization`
header to your request, followed by the `Bearer` prefix and your JWT token, like
so:

```console
curl -X GET \
    --header 'Accept: application/json' \
    --header 'Authorization: Bearer <YOUR_TOKEN>' \
    'http://localhost:8080/ga4gh/wes/v1/runs' 
```

If you are making use of the Swagger UI, you will need to click on the
**Authorize** button (which appears on the right-hand side of the top bar upon
enabling the `authorization_required` option) of the Swagger UI website and
enter your JWT token in the `api_key` field, preceded by the `Bearer` prefix:

![api_key](images/auth.png)

## Contributing

This project is a community effort and lives off your contributions, be it in
the form of bug reports, feature requests, discussions, or fixes and other code
changes. Please refer to our organization's [contributing
guidelines][res-elixir-cloud-contributing] if you are interested to contribute.
Please mind the [code of conduct][res-elixir-cloud-coc] for all interactions
with the community.

## Versioning

Development of the app is currently still in beta stage, and current
versions are for internal use only. We are aiming to have a fully
spec-compliant version of the app available soon. The plan is to then adopt a
[semantic versioning][res-semver] scheme in which we would shadow WES spec
versioning, with added date stamp patches for any patch-level changes to our
service.

## License

This project is covered by the [Apache License 2.0][license-apache] also
[shipped with this repository][license].

## Contact

The project is a collaborative effort under the umbrella of [ELIXIR Cloud &
AAI][org-elixir-cloud]. Follow the link to get in touch with us via chat or
email. Please mention the name of this service for any inquiry, proposal,
question etc.

[badge-ci]: <https://travis-ci.com/elixir-cloud-aai/cwl-WES.svg?branch=dev>
[badge-health]: <https://img.shields.io/website?url=https%3A%2F%2Fcsc-wes.rahtiapp.fi%2Fga4gh%2Fwes%2Fv1%2Fui%2F>
[badge-license]: <https://img.shields.io/badge/license-Apache%202.0-orange.svg?style=flat&color=important>
[badge-url-ci]: <https://travis-ci.com/elixir-cloud-aai/cwl-WES>
[badge-url-health]: <https://csc-wes.rahtiapp.fi/ga4gh/wes/v1/ui/>
[badge-url-license]: <http://www.apache.org/licenses/LICENSE-2.0>
[config-app]: cwl_wes/config.yaml
[docs-kubernetes]: deployment/README.md
[elixir-aai]: https://perun.elixir-czech.cz/
[elixir-user-group-apply]: https://perun.elixir-czech.cz/fed/registrar/?vo=elixir&group=ECP_CLN:OSS
[license]: LICENSE
[license-apache]: <https://www.apache.org/licenses/LICENSE-2.0>
[org-elixir-cloud]: <https://github.com/elixir-cloud-aai/elixir-cloud-aai>
[org-ga4gh]: <https://www.ga4gh.org/>
[res-connexion]: <https://github.com/zalando/connexion>
[res-cwl]: <https://www.commonwl.org/>
[res-cwl-tes]: <https://github.com/ohsu-comp-bio/cwl-tes>
[res-elixir-aai]: <https://www.elixir-europe.org/services/compute/aai>
[res-elixir-cloud-coc]: <https://github.com/elixir-cloud-aai/elixir-cloud-aai/blob/dev/CODE_OF_CONDUCT.md>
[res-elixir-cloud-contributing]: <https://github.com/elixir-cloud-aai/elixir-cloud-aai/blob/dev/CONTRIBUTING.md>
[res-elixir-cloud-resources]: <https://github.com/elixir-cloud-aai/elixir-cloud-aai/blob/dev/resources/resources.md>
[res-fair]: <https://www.go-fair.org/fair-principles/>
[res-flask]: <http://flask.pocoo.org/>
[res-funnel]: <https://ohsu-comp-bio.github.io/funnel/>
[res-ga4gh-tes]: <https://github.com/ga4gh/task-execution-schemas>
[res-ga4gh-wes]: <https://github.com/ga4gh/workflow-execution-service-schemas>
[res-gunicorn]: <https://gunicorn.org/>
[res-jwt-rfc]: <https://tools.ietf.org/html/rfc7519>
[res-mongo]: <https://www.mongodb.com/>
[res-semver]: <https://semver.org/>
[res-tesk]: <https://github.com/EMBL-EBI-TSI/TESK>
