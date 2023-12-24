import requests
from unittest import TestCase
from urllib3 import encode_multipart_formdata

from mock_data import (
    EXPECTED_SUCCESS_CODE,
    EXPECTED_ERROR_404_CODE,
    MOCK_GET_HEADERS,
    MOCK_POST_HEADERS,
    MOCK_GET_RUN_ENDPOINT,
    MOCK_GET_RUNS_ENDPOINT,
    MOCK_GET_RUN_STATUS_ENDPOINT,
    MOCK_POST_RUN_VALID_PAYLOAD,
    MOCK_SERVICE_INFO_ENDPOINT,
    RUN_ID_INVALID,
)


class TestCWLWesFetchEndpoints(TestCase):
    
    def __init__(self):
        super().__init__(self)
        self.success_workfow = None
    
    def test_cwl_wes_endpoint(self):
        
        # Test GET /service-info
        self.run_get_endpoints(
            MOCK_SERVICE_INFO_ENDPOINT, MOCK_GET_HEADERS,
            EXPECTED_SUCCESS_CODE
        )
        
        # Test GET /runs
        self.run_get_endpoints(
            MOCK_GET_RUNS_ENDPOINT, MOCK_GET_HEADERS,
            EXPECTED_SUCCESS_CODE
        )
        
        # Test GET /runs/{run_id} 404
        self.run_get_endpoints(
            MOCK_GET_RUN_ENDPOINT.format(RUN_ID_INVALID),
            MOCK_GET_HEADERS, EXPECTED_ERROR_404_CODE
        )
        
        # Test GET /runs/{run_id}/status 404
        self.run_get_endpoints(
            MOCK_GET_RUN_STATUS_ENDPOINT.format(RUN_ID_INVALID),
            MOCK_GET_HEADERS, EXPECTED_ERROR_404_CODE
        )
        
        # Test POST /runs 200
        self.run_post_endpoints(
            endpoint=MOCK_GET_RUNS_ENDPOINT,
            form_data=MOCK_POST_RUN_VALID_PAYLOAD,
            headers=MOCK_POST_HEADERS,
            expectedResponse=EXPECTED_SUCCESS_CODE
        )
    
    def run_get_endpoints(self, endpoint, headers, expectedResponse):
        response = requests.get(endpoint, headers=headers)
        assert response.status_code == expectedResponse
        
    def run_post_endpoints(self, endpoint, form_data, headers, expectedResponse):
        data, multipart_content_type = encode_multipart_formdata(form_data)
        headers["Content-Type"] = multipart_content_type
        response = requests.post(endpoint, headers=headers, data=data)
        assert response.status_code == expectedResponse


# # Fetch latest run identifier
# ENDPOINT="/runs"
# METHOD="GET"
# echo -n "Fetching run identifier | Identifier: "
# RUN_ID_COMPLETE=$(curl \
#   --silent \
#   --request "$METHOD" \
#   --header "Accept: application/json" \
#   "${WES_ROOT}${ENDPOINT}" \
#   | jq .runs[0].run_id \
#   | tr -d '"' \
# )
# echo -n "$RUN_ID_COMPLETE | Result: "
# test $RUN_ID_COMPLETE != "null" && echo "PASSED" || (echo "FAILED" && exit 1)

# # GET /runs/{run_id}/status 200
# ENDPOINT="/runs/$RUN_ID_COMPLETE"
# METHOD="GET"
# EXPECTED_CODE="200"
# echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
# RESPONSE_CODE=$(curl \
#   --silent \
#   --write-out "%{http_code}" \
#   --output "/dev/null" \
#   --request "$METHOD" \
#   --header "Accept: application/json" \
#   "${WES_ROOT}${ENDPOINT}" \
# )
# echo -n "$RESPONSE_CODE | Result: "
# test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# # GET /runs/{run_id}/status 200
# ENDPOINT="/runs/$RUN_ID_COMPLETE/status"
# METHOD="GET"
# EXPECTED_CODE="200"
# echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
# RESPONSE_CODE=$(curl \
#   --silent \
#   --write-out "%{http_code}" \
#   --output "/dev/null" \
#   --request "$METHOD" \
#   --header "Accept: application/json" \
#   "${WES_ROOT}${ENDPOINT}" \
# )
# echo -n "$RESPONSE_CODE | Result: "
# test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# # POST /runs 200
# ENDPOINT="/runs"
# METHOD="POST"
# EXPECTED_CODE="200"
# echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
# RESPONSE_CODE=$(curl \
#   --silent \
#   --write-out '%{http_code}' \
#   --output /dev/null \
#   --request "$METHOD" \
#   --header "Accept: application/json" \
#   --header "Content-Type: multipart/form-data" \
#   --form workflow_params='{"input":{"class":"File","path":"https://raw.githubusercontent.com/uniqueg/cwl-example-workflows/master/hashsplitter-workflow.cwl"}}' \
#   --form workflow_type="CWL" \
#   --form workflow_type_version="v1.0" \
#   --form workflow_url="https://github.com/uniqueg/cwl-example-workflows/blob/master/hashsplitter-workflow.cwl" \
#   "${WES_ROOT}${ENDPOINT}"
# )
# echo -n "$RESPONSE_CODE | Result: "
# test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# # Fetch latest run identifier
# ENDPOINT="/runs"
# METHOD="GET"
# echo -n "Fetching run identifier | Identifier: "
# RUN_ID_CANCEL=$(curl \
#   --silent \
#   --request "$METHOD" \
#   --header "Accept: application/json" \
#   "${WES_ROOT}${ENDPOINT}" \
#   | jq .runs[0].run_id \
#   | tr -d '"' \
# )
# echo -n "$RUN_ID_CANCEL | Result: "
# test $RUN_ID_CANCEL != "null" && echo "PASSED" || (echo "FAILED" && exit 1)

# # TODO
# # CANCEL /runs/{run_id} 200
# ENDPOINT="/runs/$RUN_ID_CANCEL/cancel"
# METHOD="POST"
# EXPECTED_CODE="200"
# echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_CODE | Got: "
# RESPONSE_CODE=$(curl \
#   --silent \
#   --write-out "%{http_code}" \
#   --output "/dev/null" \
#   --request "$METHOD" \
#   --header "Accept: application/json" \
#   "${WES_ROOT}${ENDPOINT}" \
# )
# echo -n "$RESPONSE_CODE | Result: "
# test $RESPONSE_CODE = $EXPECTED_CODE && echo "PASSED" || (echo "FAILED" && exit 1)

# # Sleep 2 seconds
# sleep 2

# # Check that status changed to CANCELING
# ENDPOINT="/runs/$RUN_ID_CANCEL/status"
# METHOD="GET"
# EXPECTED_STATUS="CANCELING"
# echo -n "Testing '$METHOD $ENDPOINT' | Expecting: $EXPECTED_STATUS | Got: "
# RESPONSE_STATUS=$(curl \
#   --silent \
#   --request "$METHOD" \
#   --header "Accept: application/json" \
#   "${WES_ROOT}${ENDPOINT}" \
#   | jq .state \
#   | tr -d '"' \
# )
# echo -n "$RESPONSE_STATUS | Result: "
# test $RESPONSE_STATUS = $EXPECTED_STATUS && echo "PASSED" || (echo "FAILED" && exit 1)