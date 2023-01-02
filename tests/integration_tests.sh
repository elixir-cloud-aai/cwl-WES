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
RUN_ID="INVALID_ID"
ENDPOINT="/runs/$RUN_ID"
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
RUN_ID="INVALID_ID"
ENDPOINT="/runs/$RUN_ID/status"
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

# GET /runs; fetch latest run identifier
ENDPOINT="/runs"
METHOD="GET"
echo -n "Fetching run identifier | Identifier: "
RUN_ID=$(curl \
  --silent \
  --request "$METHOD" \
  --header "Accept: application/json" \
  "${WES_ROOT}${ENDPOINT}" \
  | jq .runs[1].run_id \
  | tr -d '"' \
)
echo -n "$RUN_ID | Result: "
test $RUN_ID != "null" && echo "PASSED" || (echo "FAILED" && exit 1)

# GET /runs/{run_id}/status 200
ENDPOINT="/runs/$RUN_ID"
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
ENDPOINT="/runs/$RUN_ID/status"
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

# TODO
# POST /runs 200 (as above)
# Fetch identifier (as above)
# CANCEL /runs/{run_id} 200
# Check that status changed to CANCELING
# Sleep 3-5 min
# Check that second run has status CANCELED
# Check that second run has status COMPLETE
