import os
import string

from json import dump
from pymongo.errors import DuplicateKeyError
from random import choice

import wes_elixir.services.db as db

from wes_elixir.services.errors import BadRequest, WorkflowNotFound
from wes_elixir.app import cnx_app, db_runs, db_service_info
from wes_elixir.ga4gh.wes.utils_misc import immutable_multi_dict_to_nested_dict


# SET PARAMETERS
index_field = 'run_id'


def __create_run_id():
    '''Create random run id'''

    # Get run id configuration options
    charset = eval(cnx_app.app.config['database']['run_id']['charset'])
    length = cnx_app.app.config['database']['run_id']['length']

    # Return run id
    return ''.join(choice(charset) for __ in range(length))


def __init_run_document(request):
    '''Initialize workflow run document'''

    # Initialize document
    document = dict()

    # Add required keys
    document['request'] = request
    document['state'] = "UNKNOWN"
    document['run_log'] = dict()
    document['task_logs'] = list()
    document['outputs'] = dict()

    # Return run document
    return(document)


def __validate_run_request(form_data):
    '''Validate presence and types of workflow run request form data; sets defaults for optional'''

    # The form data is not validated properly because all types except 'workflow_attachment' are string and none are labeled as required
    # Considering the 'RunRequest' model in the current specs (0.3.0), the following assumptions are made and verified for the indicated parameters:
    # workflow_params:
    #   type = dict
    #   required = True
    # workflow_type:
    #   type = str
    #   required = True
    # workflow_type_version:
    #   type = str
    #   required = True
    # tags:
    #   type = dict
    #   required = False
    # workflow_engine_parameters:
    #   type = dict
    #   required = False
    # workflow_url:
    #   type = str
    #   required = True 
    # workflow_attachment:
    #   type = [str]
    #   required = False

    # Set required parameters
    required = {'workflow_params', 'workflow_type', 'workflow_type_version', 'workflow_url'}
    type_str = dict((key, form_data[key]) for key in ['workflow_type', 'workflow_type_version', 'workflow_url'] if key in form_data)
    type_dict = dict((key, form_data[key]) for key in ['workflow_params', 'workflow_engine_parameters', 'tags'] if key in form_data)
    # TODO: implement type casting/checking for workflow attachment

    # Raise error if any required params are missing
    if not required <= set(form_data):
        raise BadRequest()

    # Raise error if any string params are not of type string
    if not all(isinstance(value, str) for value in type_str.values()):
        raise BadRequest()

    # Raise error if any dict params are not of type dict
    if not all(isinstance(value, dict) for value in type_dict.values()):
        raise BadRequest()


def __check_service_info_compatibility(form_data):
    '''Check compatibility with service info; raise bad request error'''
    #TODO implement me
    pass


def __manage_workflow_attachments(form_data):
    '''Extract workflow attachments from form data'''

    # Extract workflow attachments from form data dictionary
    if 'workflow_attachment' in form_data:

        # TODO: do something with form_data['workflow_attachment']

        # Strip workflow attachments from form data
        del form_data['workflow_attachment']

    # Return form data stripped of workflow attachments
    return form_data


def __run_workflow(form_data, run_dir):
    '''Helper function for `run_workflow()`'''
    # TODO: run in background

    # Create workflow parameter file
    # TODO Think about permissions
    # TODO: Catch errors
    workflow_params_json = os.path.join(run_dir, "workflow_params.json")
    with open(workflow_params_json, 'w') as f:
        dump(form_data["workflow_params"], f, ensure_ascii=False)

    # Build command
    command = [
        "cwl-tes",
        "--tes",
        cnx_app.app.config['tes']['url'],
        form_data['workflow_url'],
        workflow_params_json
    ]

    # Execute command
    import subprocess
    subprocess.run(command)

    # TODO: Return status
    return


def __cancel_run(run_id):
    '''Helper function for `cancel_run()`'''
    # TODO: implement logic
    return run_id


def cancel_run(run_id):
    '''Cancel running workflow'''

    # Get workflow run state
    state = db.find_one_field_by_index(db_runs, index_field, run_id, 'state')

    # Raise error if workflow run was not found
    if state is None:
        raise WorkflowNotFound

    # Cancel workflow run
    run_id = __cancel_run(run_id)

    # Return run_id
    return run_id


def get_run_log(run_id):
    '''Get detailed log information for specific run'''

    # Get worklow run log
    response = db.find_one_by_index(db_runs, index_field, run_id)

    # Raise error if workflow run was not found
    if response is None:
        raise WorkflowNotFound

    # Return response
    return response


def get_run_status(run_id):
    '''Get status information for specific run'''

    # Get workflow run state
    state = db.find_one_field_by_index(db_runs, index_field, run_id, 'state')

    # Raise error if workflow run was not found
    if state is None:
        raise WorkflowNotFound

    # Return response
    return {
        "run_id": run_id,
        "state": state
    }


def list_runs(**kwargs):
    '''Get status information for specific run'''

    # TODO: stable ordering (newest last?)
    # TODO: implement next page token

    # Fall back to default page size if not provided by user
    # TODO: uncomment when implementing pagination
    #page_size = kwargs['page_size'] if 'page_size' in kwargs else cnx_app.app.config['api_endpoints']['default_page_size']

    # Query database for workflow runs
    cursor = db.find_fields(db_runs, ['run_id', 'state'])

    # Iterate through list
    runs_list = list()
    for record in cursor:
        runs_list.append(record)

    # Return formatted response object
    return {
        "next_page_token": "token",
        "runs": runs_list
    }


def run_workflow(form_data):
    '''Execute workflow and save info to database; returns unique run id'''

    # Convert ImmutableMultiDict to nested dictionary
    form_data = immutable_multi_dict_to_nested_dict(form_data)

    # Validate workflow run request
    __validate_run_request(form_data)

    # Handle workflow attachments
    form_data = __manage_workflow_attachments(form_data)

    # Initialize run document
    document = __init_run_document(form_data)

    # Keep on trying until a unique run id was found and inserted
    while True:

        # Create unique run id and add to document
        document['run_id'] = __create_run_id()

        # Try to create workflow run directory
        try:
            # TODO: Think about permissions
            # TODO: Add this to document
            run_dir = os.path.join(cnx_app.app.config['storage']['tmp_dir'], document['run_id'])
            os.mkdir(run_dir)

        # Try new run id if directory already exists
        except FileExistsError:
            continue

        # Try to insert document into database
        try:
            db_runs.insert(document)

        # Try new run id if document already exists
        except DuplicateKeyError:

            # And try to remove run directory created previously
            try:
                rmdir(run_dir)
            except OSError:
                # TODO: Log warning (run directory that was just created is not empty anymore; or 
                # other error)
                continue

            continue

        # Exit loop
        break

    # Start workflow run in background
    __run_workflow(form_data, run_dir)

    # Return run id
    return document['run_id']
