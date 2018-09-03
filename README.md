# Synopsis

[Flask](http://flask.pocoo.org/) miscroservice implementing the [Global Alliance for Genomics and Health](https://www.ga4gh.org/) (GA4GH) [Workflow Execution Service](https://github.com/ga4gh/workflow-execution-service-schemas) (WES) API specification.

# Description

This microservice uses [Flask](http://flask.pocoo.org/) and [connexion](https://github.com/zalando/connexion) to render the [GA4GH WES OpenAPI specification](https://github.com/ga4gh/workflow-execution-service-schemas). It allows users to send their workflows for execution, list current and previous workflow runs, and get the status and/or detailed information on individual workflow runs. It interprets workflows and breaks them down to individual tasks, for each task emitting a request that is compatible with the [GA4GH Task Execution Service](https://github.com/ga4gh/task-execution-schemas) (TES) OpenAPI specification. Thus, for end-to-end execution of workflows, a local or remote instance of a TES service such as [TESK](https://github.com/EMBL-EBI-TSI/TESK) or [funnel](https://ohsu-comp-bio.github.io/funnel/) is required.

The service will be backed by a [MongoDB](https://www.mongodb.com/) database and will use [ELIXIR AAI](https://www.elixir-europe.org/services/compute/aai) authentication. It will provide an abstract middleware layer providing support for various workflow languages. Once implemented, support for individual languages can be added in the form of pluggable modules. Initially, we are planning to take advantage of [CWL-TES](https://github.com/common-workflow-language/cwl-tes) to provide support for the [Common Workflow Language](https://github.com/common-workflow-language/common-workflow-language) (CWL).

Note that this project is a work in progress. **The release of a functional prototype is planned for the first week of October 2018.** See [here](https://git.scicore.unibas.ch/krini/krini-cwl/tree/dev) for a rudimentary, yet functional TES-independent WES implementation leveraging [Toil](https://github.com/DataBiosphere/toil).

# Installation

## Docker

### Requirements
* Docker
* docker-compose

### Instructions

Coming soon...

## Non-dockerized

### Requirements
* curl
* MongoDB
* Python3
* RabbitMQ
* virtualenv

### Instructions

Clone repository
```bash
git clone https://github.com/elixir-europe/WES-ELIXIR.git
```

Traverse to project directory
```bash
cd WES-ELIXIR
```

Create and activate virtual environment
```bash
virtualenv -p `which python3` venv
source venv/bin/activate
```

Install required packages
```bash
pip install -r requirements.txt
```

Clone CWL-TES repository, checkout specific version, patch & install
```bash
git clone https://github.com/common-workflow-language/cwl-tes.git
cd cwl-tes
git checkout e94d2162b6f7c86bdb7a7c90b3362d6a5163200b
bash ../patches/apply_patches.sh
python setup.py install
cd ..
```

Start MongoDB daemon
```bash
sudo service mongod start
```

Install service
```bash
python setup.py develop
```

Set config file environment variable and optionally edit config file
```bash
export WES_CONFIG="$PWD/wes_elixir/config.yaml"
```

Start service
```bash
python wes_elixir/app.py
```

Visit Swagger UI
```
<http://localhost:7777/ga4gh/wes/v1/ui>
```
Note: If you have edited `WES_CONFIG`, ensure that host and port match the values specified in the 
config file.


# Q&A

Coming soon...

# Contributing

**Join us at the [2018 BioHackathon in Paris](https://bh2018paris.info/), organized by [ELIXIR Europe](https://www.elixir-europe.org/) (November 12-16)!** Check out our [project description](https://github.com/elixir-europe/BioHackathon/tree/master/tools/Development%20of%20a%20GA4GH-compliant%2C%20language-agnostic%20workflow%20execution%20service).

This project is a community effort and lives off your contributions, be it in the form of bug
reports, feature requests, discussions, or fixes and other code changes. Please read [these
guidelines](CONTRIBUTING.md) if you want to contribute. And please mind the [code of
conduct](CODE_OF_CONDUCT.md) for all interactions with the community.

# Versioning

Coming soon...

# License

This project is covered by the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) also [shipped with this repository](LICENSE).

# Contact

The project is a collaborative effort under the umbrella of [ELIXIR
Europe](https://www.elixir-europe.org/).

Please contact the [project leader](mailto:alexander.kanitz@sib.swiss) for inquiries,
proposals, questions etc. that are not covered by the [Q&A](#Q&A) and [Contributing](#Contributing)
sections.

# References

- https://www.elixir-europe.org/
- https://www.ga4gh.org/
- https://github.com/ga4gh/workflow-execution-service-schemas
