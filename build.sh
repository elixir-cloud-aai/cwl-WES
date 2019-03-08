#!/bin/sh
# docker login -u dolphy -p __DOCKER_REGISTRY_PASS_ hx-dee-dtr01.caas.ebi.ac.uk
docker build -t dolphyvn/wes-elixir .
docker push dolphyvn/wes-elixir