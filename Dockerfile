##### BASE IMAGE #####
FROM python:3.6-slim-stretch

##### METADATA #####
LABEL base.image="python:3.6-slim-stretch"
LABEL version="1.1"
LABEL software="WES-ELIXIR"
LABEL software.version="1.0"
LABEL software.description="Flask microservice implementing the Global Alliance for Genomics and Health (GA4GH) Workflow Execution Service (WES) API specification."
LABEL software.website="https://github.com/EMBL-EBI-TSI/WES-ELIXIR"
LABEL software.documentation="https://github.com/EMBL-EBI-TSI/WES-ELIXIR"
LABEL software.license="https://github.com/EMBL-EBI-TSI/WES-ELIXIR/blob/master/LICENSE"
LABEL software.tags="General"
LABEL maintainer="foivos.gypas@unibas.ch"
LABEL maintainer.organisation="Biozentrum, University of Basel"
LABEL maintainer.location="Klingelbergstrasse 50/70, CH-4056 Basel, Switzerland"
LABEL maintainer.lab="Zavolan Lab"
LABEL maintainer.license="https://spdx.org/licenses/Apache-2.0"

# Python UserID workaround for OpenShift/K8S
ENV LOGNAME=ipython
ENV USER=ipython

RUN apt-get update && apt-get install -y nodejs openssl git build-essential python3-dev

WORKDIR /app

COPY . /app

RUN cd /app \
  && pip install --no-cache-dir -r requirements.txt \
  && python setup.py develop \
  && cd /app/src/cwl-tes \
  && python setup.py develop \
  && cd /app/src/cwltool \
  && python setup.py develop \
  && cd /app/src/py-tes \
  && python setup.py develop \
  && cd /

# 
# 'cwl-tes' pulls the wrong version of cwltool, so we have to override it here.
# 
# In its requirements.txt, it pins a specific version ('cwltool==1.0.20180912090223'), but in setup.py it says 'cwltool>=x' 
# -- which makes pip pull the latest one. Which breaks things.
# 
RUN pip install cwltool==1.0.20181217162649
