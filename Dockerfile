##### BASE IMAGE #####
FROM ubuntu:16.04

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

## Install system resources & dependencies
RUN apt-get update \
  && apt-get install -y build-essential checkinstall libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev zlib1g-dev openssl libffi-dev python3-dev python3-setuptools git wget curl nodejs

## Install Python
RUN wget https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tar.xz \
  && tar xJf Python-3.6.0.tar.xz \
  && cd Python-3.6.0 \
  && ./configure \
  && make altinstall \
  && ln -s /Python-3.6.0/python /usr/local/bin \
  && cd .. \
  && python -m pip install --upgrade pip setuptools wheel virtualenv

## Copy app requirements
COPY ./requirements.txt /app

## Install app dependencies
RUN cd /app \
  && pip install -r requirements.txt \
  && cd /app/src/cwl-tes \
  && python setup.py develop \
  && cd /app

## Copy remaining app files
COPY ./ .

## Install app
RUN python setup.py develop \
  && cd /

## Copy FTP server credentials
COPY .netrc /root
