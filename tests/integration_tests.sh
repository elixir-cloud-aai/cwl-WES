#!/usr/bin/env bash

set -euo pipefail

WES_ROOT="http://localhost:8080/ga4gh/wes/v1"

# GET /service-info
ENDPOINT="/service-info"
METHOD="GET"
EXPECTED_CODE="200"
echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
RESPONSE_CODE=$(curl \
  --silent \
  --write-out "%{http_code}" \
  --output "/dev/null" \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
)
echo -n "$RESPONSE_CODE | Result: "
test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# GET /runs
ENDPOINT="/runs"
METHOD="GET"
EXPECTED_CODE="200"
echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
RESPONSE_CODE=$(curl \
  --silent \
  --write-out "%{http_code}" \
  --output "/dev/null" \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
)
echo -n "$RESPONSE_CODE | Result: "
test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# GET /runs/{run_id} 404
RUN_ID_INVALID="INVALID_ID"
ENDPOINT="/runs/$RUN_ID_INVALID"
METHOD="GET"
EXPECTED_CODE="404"
echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
RESPONSE_CODE=$(curl \
  --silent \
  --write-out "%{http_code}" \
  --output "/dev/null" \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
)
echo -n "$RESPONSE_CODE | Result: "
test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# GET /runs/{run_id}/status 404
RUN_ID_INVALID="INVALID_ID"
ENDPOINT="/runs/$RUN_ID_INVALID/status"
METHOD="GET"
EXPECTED_CODE="404"
echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
RESPONSE_CODE=$(curl \
  --silent \
  --write-out "%{http_code}" \
  --output "/dev/null" \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
)
echo -n "$RESPONSE_CODE | Result: "
test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# POST /runs 200
ENDPOINT="/runs"
METHOD="POST"
EXPECTED_CODE="200"
echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
RESPONSE_CODE=$(curl \
  --silent \
  --write-out '%{http_code}' \
  --output /dev/null \
  --request "$METHOD" \
  --header "Accept: application/json" \
  --header "Content-Type: multipart/form-data" \
  --form workflow_params='{"input":{"class":"File","path":"https://raw.githubusercontent.com/uniqueg/cwl-example-workflows/master/hashsplitter-workflow.cwl"}}' \
  --form workflow_type="CWL" \
  --form workflow_type_version="v1.0" \
  --form workflow_url="https://github.com/uniqueg/cwl-example-workflows/blob/master/hashsplitter-workflow.cwl" \
  "${WES_ROOT}${ENDPOINT}"
)
echo -n "$RESPONSE_CODE | Result: "
test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# Fetch latest run identifier
ENDPOINT="/runs"
METHOD="GET"
echo -n "Fetching run identifier | Identifier: "
RUN_ID_COMPLETE=$(curl \
  --silent \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
  | jq .runs[0].run_id \
  | tr -d '"' \
)
echo -n "$RUN_ID_COMPLETE | Result: "
test $RUN_ID_COMPLETE != "null" && echo "PASSED" || (echo "FAILED" && exit 1)

# GET /runs/{run_id}/status 200
ENDPOINT="/runs/$RUN_ID_COMPLETE"
METHOD="GET"
EXPECTED_CODE="200"
echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
RESPONSE_CODE=$(curl \
  --silent \
  --write-out "%{http_code}" \
  --output "/dev/null" \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
)
echo -n "$RESPONSE_CODE | Result: "
test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# GET /runs/{run_id}/status 200
ENDPOINT="/runs/$RUN_ID_COMPLETE/status"
METHOD="GET"
EXPECTED_CODE="200"
echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
RESPONSE_CODE=$(curl \
  --silent \
  --write-out "%{http_code}" \
  --output "/dev/null" \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
)
echo -n "$RESPONSE_CODE | Result: "
test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# POST /runs 200
ENDPOINT="/runs"
METHOD="POST"
EXPECTED_CODE="200"
echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
RESPONSE_CODE=$(curl \
  --silent \
  --write-out '%{http_code}' \
  --output /dev/null \
  --request "$METHOD" \
  --header "Accept: application/json" \
  --header "Content-Type: multipart/form-data" \
  --form workflow_params='{"input":{"class":"File","path":"https://raw.githubusercontent.com/uniqueg/cwl-example-workflows/master/hashsplitter-workflow.cwl"}}' \
  --form workflow_type="CWL" \
  --form workflow_type_version="v1.0" \
  --form workflow_url="https://github.com/uniqueg/cwl-example-workflows/blob/master/hashsplitter-workflow.cwl" \
  "${WES_ROOT}${ENDPOINT}"
)
echo -n "$RESPONSE_CODE | Result: "
test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# Fetch latest run identifier
ENDPOINT="/runs"
METHOD="GET"
echo -n "Fetching run identifier | Identifier: "
RUN_ID_CANCEL=$(curl \
  --silent \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
  | jq .runs[0].run_id \
  | tr -d '"' \
)
echo -n "$RUN_ID_CANCEL | Result: "
test $RUN_ID_CANCEL != "null" && echo "PASSED" || (echo "FAILED" && exit 1)

# TODO
# CANCEL /runs/{run_id} 200
# Check that status changed to CANCELING
# Sleep 3-5 min
# Check that run with $RUN_ID_COMPLETE has status COMPLETE
# Check that run with $RUN_ID_CANCEL has status CANCELED
