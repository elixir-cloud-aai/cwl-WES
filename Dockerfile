##### BASE IMAGE #####
FROM python:slim-stretch

##### METADATA #####
LABEL base.image="ubuntu:16.04"
LABEL version="1.1"
LABEL software="WES-ELIXIR"
LABEL software.version="1.0"
LABEL software.description="Flask microservice implementing the Global Alliance for Genomics and Health (GA4GH) Workflow Execution Service (WES) API specification."
LABEL software.website="https://github.com/elixir-europe/WES-ELIXIR"
LABEL software.documentation="https://github.com/elixir-europe/WES-ELIXIR"
LABEL software.license="https://github.com/elixir-europe/WES-ELIXIR/blob/master/LICENSE"
LABEL software.tags="General"
LABEL maintainer="foivos.gypas@unibas.ch"
LABEL maintainer.organisation="Biozentrum, University of Basel"
LABEL maintainer.location="Klingelbergstrasse 50/70, CH-4056 Basel, Switzerland"
LABEL maintainer.lab="Zavolan Lab"
LABEL maintainer.license="https://spdx.org/licenses/Apache-2.0"


RUN apt-get update && apt-get install -y nodejs openssl git build-essential python3-dev

## Copy app files
ADD ./ /app

## Install dependencies
RUN cd /app \
  && pip install -r requirements.txt \
  && python setup.py develop \
  && cd /app/src/cwl-tes \
  && python setup.py develop \
  && cd /app/src/cwltool \
  && python setup.py develop \
  && cd /app/src/py-tes \
  && python setup.py develop \
  && cd /
