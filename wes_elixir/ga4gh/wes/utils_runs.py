import os
import string
import subprocess

from json import decoder, dump, loads
from pymongo.errors import DuplicateKeyError
from random import choice

import wes_elixir.database.utils as db_utils

from wes_elixir.errors.errors import BadRequest, WorkflowNotFound
from wes_elixir.celery_worker import celery
from wes_elixir.ga4gh.wes.utils_bg_tasks import add_run_to_task_queue


#############################
### DELETE /runs/<run_id> ###
#############################

def cancel_run(config, run_id):
    '''Cancel running workflow'''

    # Re-assign config values
    collection_runs = config['database']['collections']['runs']
    index_field = config['runs_index_field']['run_id']

    # Get workflow run state
    state = db_utils.find_one_field_by_index(collection_runs, index_field, run_id, 'state')

    # Raise error if workflow run was not found
    if state is None:
        raise WorkflowNotFound

    # Cancel workflow run
    __cancel_run(run_id)
    
    # Build formatted response object
    response = {"run_id": run_id}

    # Return response object
    return response


def __cancel_run(run_id):
    '''Helper function for `cancel_run()`'''
    # TODO: implement logic
    
    # Nothing to return
    return None


##########################
### GET /runs/<run_id> ###
##########################

def get_run_log(config, run_id):
    '''Get detailed log information for specific run'''

    # Re-assign config values
    collection_runs = config['database']['collections']['runs']
    index_field = config['runs_index_field']['run_id']

    # Get worklow run log
    response = db_utils.find_one_by_index(collection_runs, index_field, run_id)

    # Raise error if workflow run was not found
    if response is None:
        raise WorkflowNotFound

    # Return response
    return response


#################################
### GET /runs/<run_id>/status ###
#################################

def get_run_status(config, run_id):
    '''Get status information for specific run'''

    # Re-assign config values
    collection_runs = config['database']['collections']['runs']
    index_field = config['runs_index_field']['run_id']

    # Get workflow run state
    state = db_utils.find_one_field_by_index(collection_runs, index_field, run_id, 'state')

    # Raise error if workflow run was not found
    if state is None:
        raise WorkflowNotFound

    # Build formatted response object
    response = {
        "run_id": run_id,
        "state": state
    }
    
    # Return response object
    return response


#################
### GET /runs ###
#################

def list_runs(config, **kwargs):
    '''Get status information for specific run'''

    # Re-assign config values
    collection_runs = config['database']['collections']['runs']

    # TODO: stable ordering (newest last?)
    # TODO: implement next page token

    # Fall back to default page size if not provided by user
    # TODO: uncomment when implementing pagination
    #page_size = kwargs['page_size'] if 'page_size' in kwargs else cnx_app.app.config['api_endpoints']['default_page_size']

    # Query database for workflow runs
    cursor = db_utils.find_fields(collection_runs, ['run_id', 'state'])

    # Iterate through list
    runs_list = list()
    for record in cursor:
        runs_list.append(record)

    # Build formatted response object
    response = {
        "next_page_token": "token",
        "runs": runs_list
    }

    # Return response object
    return response


##################
### POST /runs ###
##################

def run_workflow(config, form_data):
    '''Execute workflow and save info to database; returns unique run id'''

    # Arrange form data in dictionary
    form_data = __immutable_multi_dict_to_nested_dict(multi_dict=form_data)

    # Validate workflow run request
    __validate_run_workflow_request(data=form_data)

    # Check compatibility with service info
    __check_service_info_compatibility(data=form_data)

    # Handle workflow attachments
    form_data = __process_workflow_attachments(data=form_data)

    # Initialize run document
    document = __init_run_document(data=form_data)

    # Create run environment
    document = __create_run_environment(config=config, document=document)

    # Start workflow run in background
    # tmp_dir and out_dir need to go in document
    # tes_url c
    __run_workflow(config=config, document=document)

    # Build formatted response object
    response = {"run_id": document['run_id']} 

    # Return response object
    return response


def __immutable_multi_dict_to_nested_dict(multi_dict):
    '''Convert ImmutableMultiDict to nested dictionary'''

    # Convert ImmutableMultiDict to flat dictionary
    nested_dict = multi_dict.to_dict(flat=True)

    # Iterate over key in dictionary
    for key in nested_dict:

        # Try to decode JSON string; ignore JSONDecodeErrors
        try:
            nested_dict[key] = loads(nested_dict[key])

        except decoder.JSONDecodeError:
            pass

    # Return formatted request dictionary
    return nested_dict


def __validate_run_workflow_request(data):
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
    type_str = dict((key, data[key]) for key in ['workflow_type', 'workflow_type_version', 'workflow_url'] if key in data)
    type_dict = dict((key, data[key]) for key in ['workflow_params', 'workflow_engine_parameters', 'tags'] if key in data)
    # TODO: implement type casting/checking for workflow attachment

    # Raise error if any required params are missing
    if not required <= set(data):
        raise BadRequest()

    # Raise error if any string params are not of type string
    if not all(isinstance(value, str) for value in type_str.values()):
        raise BadRequest()

    # Raise error if any dict params are not of type dict
    if not all(isinstance(value, dict) for value in type_dict.values()):
        raise BadRequest()
    
    # Nothing to return
    return None


def __check_service_info_compatibility(data):
    '''Check compatibility with service info; raise bad request error'''
    # TODO: implement me
    return None


def __process_workflow_attachments(data):
    '''Extract workflow attachments from form data'''

    # Extract workflow attachments from form data dictionary
    if 'workflow_attachment' in data:

        # TODO: do something with data['workflow_attachment']

        # Strip workflow attachments from data
        del data['workflow_attachment']


###################################################################################################################
# WORK HERE

    # Workaround until processing of workflow attachments is implemented
    # The path to the (main) CWL workflow file is taken from 
    # TODO: TEMPORARILY DO THIS (in __process_worklflow_attachments):
    # TODO: Create workflow parameter file => document['internal']['yaml_path']
    # TODO: Create (main) workflow file => use form_data['workflow_url'] (change to document['api']['workflow_url']) => document['internal']['yaml_path']
#    workflow_params_json = os.path.join(run_dir, "workflow_params.json")
#    with open(workflow_params_json, 'w') as f:
#        dump(form_data["workflow_params"], f, ensure_ascii=False)
#
#    cwl_path = form_data['workflow_url']

###################################################################################################################

    # Return form data stripped of workflow attachments
    return data


def __init_run_document(data):
    '''Initialize workflow run document'''

    # Initialize document
    document = dict()

    # Add required keys
    document['request'] = data
    document['state'] = "UNKNOWN"
    document['run_log'] = dict()
    document['task_logs'] = list()
    document['outputs'] = dict()

    # Return run document
    return document


def __create_run_environment(config, document):
    '''Create unique run identifier and permanent and temporary storage directories for current run'''

    # Re-assign config values
    collection_runs = config['database']['collections']['runs']
    out_dir = config['storage']['permanent_dir']
    tmp_dir = config['storage']['tmp_dir']

    # Keep on trying until a unique run id was found and inserted
    while True:

        # Create unique run id and add to document
        run_id = __create_run_id(config)

        # Try to create workflow run directory (temporary)
        try:
            # TODO: Think about permissions
            # TODO: Add this to document
            # TODO: Add working directory (currently one has to run the app from the outermost dir)
            current_tmp_dir = os.path.join(tmp_dir, run_id)
            os.mkdir(current_tmp_dir)

        # Try new run id if directory already exists
        except FileExistsError:
            continue

        # Try to create output directory (permanent)
        try:
            # TODO: Think about permissions
            # TODO: Add this to document
            # TODO: Add working directory (currently one has to run the app from the outermost dir)
            current_out_dir = os.path.join(out_dir, run_id)
            os.mkdir(current_out_dir)

        # Try new run id if directory already exists
        except FileExistsError:
            continue

        # TODO: add values to document: run_id, out_dir, tmp_dir...
        document['run_id'] = run_id

        # Try to insert document into database
        try:
            collection_runs.insert(document)

        # Try new run id if document already exists
        except DuplicateKeyError:

            # And try to remove run directory created previously
            try:
                os.rmdir(current_tmp_dir)
                os.rmdir(current_out_dir)

            # Handle race condition
            except OSError:
                # TODO: Log warning (run directory that was just created is not empty anymore; or 
                # other error)
                continue

            continue

        # Exit loop
        break

    # Return updated document
    return document


def __create_run_id(config):
    '''Create random run id'''

    # Re-assign config values
    charset = eval(config['database']['run_id']['charset'])
    length = config['database']['run_id']['length']

    # Return run id
    return ''.join(choice(charset) for __ in range(length))


def __run_workflow(config, document):
    '''Helper function for `run_workflow()`'''

    # Re-assign config values
    tes_url = config['tes']['url']

    # Re-assign document values
    cwl_path = document['internal']['cwl_path']
    yaml_path = document['internal']['yaml_path']
    tmp_dir = document['internal']['tmp_dir']
    out_dir = document['internal']['out_dir']

    # Build command
    command_list = [
        "cwl-tes",
        "--tes",
        tes_url,
        cwl_path,
        yaml_path
    ]

    # Add workflow run to task queue
    # TODO: put in try block
    add_run_to_task_queue.delay(
        config=config,
        command_list=command_list,
        cwd=tmp_dir,
        out_dir=out_dir
    )

    # Nothing to return
    return None