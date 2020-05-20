##### BASE IMAGE #####
FROM python:3.6-slim-stretch

##### METADATA #####
LABEL base.image="python:3.6-slim-stretch"
LABEL version="1.1"
LABEL software="cwl-WES"
LABEL software.version="1.0"
LABEL software.description="Flask microservice implementing the Global Alliance for Genomics and Health (GA4GH) Workflow Execution Service (WES) API specification."
LABEL software.website="https://github.com/elixir-cloud-aai/cwl-WES"
LABEL software.documentation="https://github.com/elixir-cloud-aai/cwl-WES"
LABEL software.license="https://github.com/elixir-cloud-aai/cwl-WES/blob/master/LICENSE"
LABEL software.tags="General"
LABEL maintainer="alexander.kanitz@alumni.ethz.ch"
LABEL maintainer.organisation="Biozentrum, University of Basel"
LABEL maintainer.location="Klingelbergstrasse 50/70, CH-4056 Basel, Switzerland"
LABEL maintainer.lab="ELIXIR Cloud & AAI"
LABEL maintainer.license="https://spdx.org/licenses/Apache-2.0"

# Python UserID workaround for OpenShift/K8S
ENV LOGNAME=ipython
ENV USER=ipython
ENV HOME=/tmp/user

# Install general dependencies
RUN apt-get update && apt-get install -y nodejs openssl git build-essential python3-dev curl jq

## Set working directory
WORKDIR /app

## Copy Python requirements
COPY ./requirements.txt /app/requirements.txt

## Install Python dependencies
RUN cd /app \
  && pip install -r requirements.txt \
  && cd /app/src/cwl-tes \
  && python setup.py develop \
  && cd / \
  && mkdir -p /tmp/user

## Copy remaining app files
COPY ./ /app

## Install app & set write permissions for specs directory
RUN cd /app \
  && python setup.py develop \
  && cd / \
  && chmod g+w /app/cwl_wes/api/ \
  && chmod g+w -R /tmp/user

