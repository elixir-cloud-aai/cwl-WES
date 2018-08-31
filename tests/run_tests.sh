#!/usr/bin/env bash

cwl-tes --tes https://tes-dev.tsi.ebi.ac.uk/ cwl/tools/echo.cwl cwl/tools/echo-job.json

cwl-tes --tes https://tes-dev.tsi.ebi.ac.uk/ cwl/tools/sleep.cwl cwl/tools/sleep-job.json

## Post tests

# Post: sleep command
#curl -X POST --header 'Content-Type: multipart/form-data' --header 'Accept: application/json' -F workflow_params=tests%2Fcwl%2Ftools%2Fsleep-job.yml -F workflow_type=cwl -F workflow_type_version=v1.0 -F tags=empty -F workflow_engine_parameters=empty -F workflow_url=tests%2Fcwl%2Ftools%2Fsleep.cwl -F workflow_attachment=empty  'http://localhost:7777/ga4gh/wes/v1/runs'

# Post: echo command
#curl -X POST --header 'Content-Type: multipart/form-data' --header 'Accept: application/json' -F workflow_params=tests%2Fcwl%2Ftools%2Fecho-job.yml -F workflow_type=cwl -F workflow_type_version=v1.0 -F tags=empty -F workflow_engine_parameters=empty -F workflow_url=tests%2Fcwl%2Ftools%2Fecho.cwl -F workflow_attachment=empty  'http://localhost:7777/ga4gh/wes/v1/runs'
