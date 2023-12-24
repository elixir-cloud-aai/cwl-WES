import json

# Host configs for unittests
MOCK_WES_ROOT = "http://localhost:8080/ga4gh/wes/v1"

# Headers
MOCK_GET_HEADERS = {"Accept": "application/json"}
MOCK_POST_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "multipart/form-data",
}

# Sample RUNs data
RUN_ID_INVALID = "INVALID_ID"
WORKFLOW_PARAMS_DICT = {
    "input": {
        "class":"File",
        "path":"https://raw.githubusercontent.com/uniqueg/cwl-example-workflows/master/hashsplitter-workflow.cwl"
    }
}
MOCK_POST_RUN_VALID_PAYLOAD = {
    "workflow_params": json.dumps(WORKFLOW_PARAMS_DICT),
    "workflow_type": "CWL",
    "workflow_type_version": "v1.0",
    "workflow_url": "https://github.com/uniqueg/cwl-example-workflows/blob/master/hashsplitter-workflow.cwl"
}

# Endpoints
MOCK_SERVICE_INFO_ENDPOINT = MOCK_WES_ROOT + "/service-info"
MOCK_GET_RUNS_ENDPOINT = MOCK_WES_ROOT + "/runs"
MOCK_GET_RUN_ENDPOINT = MOCK_WES_ROOT + "/runs/{}"
MOCK_GET_RUN_STATUS_ENDPOINT = MOCK_WES_ROOT + "/runs/{}/status"

# Status Codes
EXPECTED_SUCCESS_CODE = 200
EXPECTED_ERROR_404_CODE = 404