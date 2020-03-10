# cwl-WES

[![Apache License](https://img.shields.io/badge/license-Apache%202.0-orange.svg?style=flat&color=important)](http://www.apache.org/licenses/LICENSE-2.0)
[![Build_status](https://travis-ci.com/elixir-cloud-aai/cwl-WES.svg?branch=dev)](https://travis-ci.com/elixir-cloud-aai/cwl-WES)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fwes.c03.k8s-popup.csc.fi%2Fga4gh%2Fwes%2Fv1%2Fui%2F)](https://wes.c03.k8s-popup.csc.fi/ga4gh/wes/v1/ui/)

## Synopsis

[Flask](http://flask.pocoo.org/) microservice implementing the
[Global Alliance for Genomics and Health](https://www.ga4gh.org/) (GA4GH)
[Workflow Execution Service](https://github.com/ga4gh/workflow-execution-service-schemas)
(WES) API specification.

## Description

cwl-WES (formerly: WES-ELIXIR) is an implementation of the
[GA4GH WES OpenAPI specification](https://github.com/ga4gh/workflow-execution-service-schemas)
based on [Flask](http://flask.pocoo.org/) and [Connexion](https://github.com/zalando/connexion).
It allows clients/users to send workflows for execution, list current and previous workflow runs,
and get the status and/or detailed information on individual workflow runs. It interprets
workflows and breaks them down into individual tasks, for each task emitting a request that
is compatible with the [GA4GH Task Execution Service](https://github.com/ga4gh/task-execution-schemas)
(TES) OpenAPI specification. Thus, for end-to-end execution of workflows, a local or remote
instance of a TES service such as [TESK](https://github.com/EMBL-EBI-TSI/TESK) or
[funnel](https://ohsu-comp-bio.github.io/funnel/) is required.

The service is backed by a [MongoDB](https://www.mongodb.com/) database and optionally uses
[JWT](https://jwt.io/introduction/) token-based authorization, e.g. through
[ELIXIR AAI](https://www.elixir-europe.org/services/compute/aai). While currently only workflows
written in the [Common Workflow Language](https://www.commonwl.org/) are supported (leveraged
by [CWL-TES](https://github.com/common-workflow-language/cwl-tes), we are planning to abstract
workflow interpretation away from API business logic on the one hand and task execution on the
other, thus hoping to provide an abstract middleware layer that can be interfaced by any workflow
language interpreter in a pluggable manner.

Note that the project is currently still under active development.
Nevertheless, a largely [**FUNCTIONAL PROTOTYPE**](http://193.167.189.73:7777/ga4gh/wes/v1/ui/)
is available as of October 2018, hosted at the [CSC](https://www.csc.fi/home) in Helsinki.

cwl-WES is part of [ELIXIR](https://www.elixir-europe.org/), a multinational effort at
establishing and implementing FAIR data sharing and promoting reproducible data analyses and
responsible data handling in the Life Sciences. Infrastructure and IT support are provided by
ELIXIR Finland at the [CSC](https://www.csc.fi/home), the [TESK](https://github.com/EMBL-EBI-TSI/TESK)
service is being developed and maintained by ELIXIR UK at the [EBI](https://www.ebi.ac.uk/) in
Hinxton, and cwl-WES itself is being developed by ELIXIR Switzerland at the
[Biozentrum](https://www.biozentrum.unibas.ch/) in Basel and the
[Swiss Institute of Bioinformatics](https://www.sib.swiss/).

## Installation

### Kubernetes

See instructions in [the deployment directory's README.md file](deployment/README.md).

### Docker

#### Requirements

Ensure you have the following software installed:

* Docker (18.06.1-ce, build e68fc7a)
* docker-compose (1.22.0, build f46880fe)
* Git (1.8.3.1)

Note: These are the versions used for development/testing. Other versions may or may not work.

#### Instructions

##### Set up environment

Create data directory and required subdiretories

```bash
mkdir -p data/cwl_wes/db data/cwl_wes/output data/cwl_wes/tmp
```

Clone repository

```bash
git clone https://github.com/elixir-cloud-aai/cwl-WES.git app
```

Traverse to app directory

```bash
cd app
```

Place a `.netrc` file for access to a FTP server in app directory.
Don't forget to replace `<USERNAME>` and `<PASSWORD>` with real values.

```bash
cat << EOF > .netrc
machine ftp-private.ebi.ac.uk
login <USERNAME>
password <PASSWORD>
EOF
```

> If you do not know what to put here, just creating an empty file `.netrc`
> with, e.g., `touch .netrc` will be fine for testing purposes. Requirements
> for this file will hopefully soon be entirely lifted.

##### Edit/override app config (optional!)

* Via configuration files:

```bash
vi cwl_wes/config/app_config.yaml
```

* Via environment variables:

A few configuration settings can be overridden by environment variables.

```bash
export <ENV_VAR_NAME>=<VALUE>
```

* List of the available environment variables:

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

Build container image

```bash
docker-compose build
```

Run docker-compose services in detached/daemonized mode

```bash
docker-compose up -d
```

###### Use service

Visit Swagger UI

```bash
firefox http://localhost:7777/ga4gh/wes/v1/ui
```

Example values to start a simple CWL test workflow run:

- `workflow_params`: `{"input":{"class":"File","path":"ftp://ftp-private.ebi.ac.uk/upload/foivos/test.txt"}}`
- `workflow_type`: `CWL`
- `workflow_type_version`: `v1.0`
- `workflow_url`: `https://github.com/uniqueg/cwl-example-workflows/blob/master/hashsplitter-workflow.cwl`

Leave the rest of the values empty and hit the `Try it out!` button.

## Q&A

Coming soon...

## Contributing

**Join us at the [2019 BioHackathon in Paris](https://www.biohackathon-europe.org/index.html), 
organized by [ELIXIR Europe](https://www.elixir-europe.org/) (November 18-22)!** Check out our 
[project 
description](https://github.com/elixir-europe/BioHackathon-projects-2019/tree/master/projects/16).

This project is a community effort and lives off your contributions, be it in the form of bug
reports, feature requests, discussions, or fixes and other code changes. Please read [these
guidelines](CONTRIBUTING.md) if you want to contribute. And please mind the [code of
conduct](CODE_OF_CONDUCT.md) for all interactions with the community.

## Versioning

Development of the app is currently still in alpha stage, and current "versions" are for internal
use only. We are aiming to have a fully spec-compliant ("feature complete") version of the app
available by the end of 2018. The plan is to then adopt a [semantic versioning](https://semver.org/)
scheme in which we would shadow WES spec versioning for major and minor versions, and release
patched versions intermittently.

## License

This project is covered by the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) also
[shipped with this repository](LICENSE).

## Contact

The project is a collaborative effort under the umbrella of the [ELIXIR
Cloud and AAI](https://elixir-europe.github.io/cloud/) group.

Please contact the [project leader](mailto:alexander.kanitz@sib.swiss) for inquiries,
proposals, questions etc. that are not covered by the [Q&A](#Q&A) and [Contributing](#Contributing)
sections.

## References

* <https://elixir-europe.github.io/cloud/>
* <https://www.ga4gh.org/>
* <https://github.com/ga4gh/workflow-execution-service-schemas>

