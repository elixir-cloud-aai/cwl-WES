FROM elixircloud/foca:20221110-py3.7

LABEL version="1.1"
LABEL software="cwl-WES"
LABEL software.description="Trigger CWL workflows via GA4GH WES and TES"
LABEL software.website="https://github.com/elixir-cloud-aai/cwl-WES"
LABEL software.documentation="https://github.com/elixir-cloud-aai/cwl-WES"
LABEL software.license="https://spdx.org/licenses/Apache-2.0"
LABEL maintainer="cloud-service@elixir-europe.org"
LABEL maintainer.organisation="ELIXIR Cloud & AAI"

# Python UserID workaround for OpenShift/K8S
ENV LOGNAME=ipython
ENV USER=ipython

WORKDIR /app
COPY ./ .
RUN pip install -e .

## Add permissions for storing updated API specification
## (required by FOCA)
RUN chmod -R a+rwx /app/cwl_wes/api
