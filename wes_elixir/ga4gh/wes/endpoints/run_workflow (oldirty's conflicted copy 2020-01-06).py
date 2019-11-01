"""Utility functions for POST /runs endpoint."""

import logging
import os
import re
import shutil
import string  # noqa: F401
import subprocess

from celery import uuid
from json import (decoder, loads)
from pymongo.errors import DuplicateKeyError
from random import choice
from typing import Dict
from yaml import dump
from werkzeug.datastructures import ImmutableMultiDict

from wes_elixir.config.config_parser import get_conf
from wes_elixir.errors.errors import BadRequest
from wes_elixir.tasks.tasks.run_workflow import task__run_workflow


# Get logger instance
logger = logging.getLogger(__name__)


# Utility function for endpoint POST /runs
def run_workflow(
    config: Dict,
    form_data: ImmutableMultiDict,
    *args,
    **kwargs
) -> Dict:
    """Executes workflow and save info to database; returns unique run id."""
    # Validate data and prepare run environment
    form_data_dict = __immutable_multi_dict_to_nested_dict(
        multi_dict=form_data
    )
    __validate_run_workflow_request(data=form_data_dict)
    __check_service_info_compatibility(data=form_data_dict)
    document = __init_run_document(data=form_data_dict)
    document = __create_run_environment(
        config=config,
        document=document,
        **kwargs
    )

    # Start workflow run in background
    __run_workflow(
        config=config,
        document=document,
        **kwargs
    )

    response = {'run_id': document['run_id']}
    return response


def __immutable_multi_dict_to_nested_dict(
    multi_dict: ImmutableMultiDict
) -> Dict:
    """Converts ImmutableMultiDict to nested dictionary."""
    # Convert to flat dictionary
    nested_dict = multi_dict.to_dict(flat=True)
    for key in nested_dict:
        # Try to decode JSON string; ignore JSONDecodeErrors
        try:
            nested_dict[key] = loads(nested_dict[key])
        except decoder.JSONDecodeError:
            pass
    return nested_dict


def __validate_run_workflow_request(data: Dict) -> None:
    """Validates presence and types of workflow run request form data; sets
    defaults for optional fields."""
    # The form data is not validated properly because all types except
    # 'workflow_attachment' are string and none are labeled as required
    # Considering the 'RunRequest' model in the current specs (0.3.0), the
    # following assumptions are made and verified for the indicated parameters:
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
    required = {
        'workflow_params',
        'workflow_type',
        'workflow_type_version',
        'workflow_url',
    }
    params_str = [
        'workflow_type',
        'workflow_type_version',
        'workflow_url',
    ]
    params_dict = [
        'workflow_params',
        'workflow_engine_parameters',
        'tags',
    ]
    type_str = dict((key, data[key]) for key in params_str if key in data)
    type_dict = dict((key, data[key]) for key in params_dict if key in data)
    # TODO: implement type casting/checking for workflow attachment

    # Raise error if any required params are missing
    if not required <= set(data):
        logger.error('POST request does not conform to schema.')
        raise BadRequest

    # Raise error if any string params are not of type string
    if not all(isinstance(value, str) for value in type_str.values()):
        logger.error('POST request does not conform to schema.')
        raise BadRequest

    # Raise error if any dict params are not of type dict
    if not all(isinstance(value, dict) for value in type_dict.values()):
        logger.error('POST request does not conform to schema.')
        raise BadRequest

    return None


def __check_service_info_compatibility(data: Dict) -> None:
    """Checks compatibility with service info; raises BadRequest."""
    # TODO: implement me
    return None


def __init_run_document(data: Dict) -> Dict:
    """Initializes workflow run document."""
    document: Dict = dict()
    document['api'] = dict()
    document['internal'] = dict()
    document['api']['request'] = data
    document['api']['state'] = 'UNKNOWN'
    document['api']['run_log'] = dict()
    document['api']['task_logs'] = list()
    document['api']['outputs'] = dict()
    return document


def __create_run_environment(
    config: Dict,
    document: Dict,
    **kwargs
) -> Dict:
    """Creates unique run identifier and permanent and temporary storage
    directories for current run."""
    collection_runs = get_conf(config, 'database', 'collections', 'runs')
    out_dir = get_conf(config, 'storage', 'permanent_dir')
    tmp_dir = get_conf(config, 'storage', 'tmp_dir')
    run_id_charset = eval(get_conf(config, 'database', 'run_id', 'charset'))
    run_id_length = get_conf(config, 'database', 'run_id', 'length')

    # Keep on trying until a unique run id was found and inserted
    # TODO: If no more possible IDs => inf loop; fix (raise custom error; 500
    #       to user)
    while True:

        # Create unique run and task ids
        run_id = __create_run_id(
            charset=run_id_charset,
            length=run_id_length,
        )
        task_id = uuid()

        # Set temporary and output directories
        current_tmp_dir = os.path.abspath(os.path.join(tmp_dir, run_id))
        current_out_dir = os.path.abspath(os.path.join(out_dir, run_id))

        # Try to create workflow run directory (temporary)
        try:
            # TODO: Think about permissions
            # TODO: Add working dir (currently one has to run the app from
            #       outermost dir)
            os.makedirs(current_tmp_dir)
            os.makedirs(current_out_dir)

        # Try new run id if directory already exists
        except FileExistsError:
            continue

        # Add run/task/user identifier, temp/output directories to document
        document['run_id'] = run_id
        document['task_id'] = task_id
        if 'user_id' in kwargs:
            document['user_id'] = kwargs['user_id']
        else:
            document['user_id'] = None
        document['internal']['tmp_dir'] = current_tmp_dir
        document['internal']['out_dir'] = current_out_dir

        # Process worflow attachments
        document = __process_workflow_attachments(document)

        # Try to insert document into database
        try:
            collection_runs.insert(document)

        # Try new run id if document already exists
        except DuplicateKeyError:

            # And remove run directories created previously
            shutil.rmtree(current_tmp_dir, ignore_errors=True)
            shutil.rmtree(current_out_dir, ignore_errors=True)

            continue

        # Catch other database errors
        # TODO: implement properly
        except Exception as e:
            print('Database error')
            print(e)
            break

        # Exit loop
        break

    return document


def __create_run_id(
    charset: str = '0123456789',
    length: int = 6
) -> str:
    """Creates random run ID."""
    return ''.join(choice(charset) for __ in range(length))


def __process_workflow_attachments(data: Dict) -> Dict:
    """Processes workflow attachments."""
    # TODO: implement properly
    # Current workaround until processing of workflow attachments is
    # implemented
    # Use 'workflow_url' for path to (main) CWL workflow file on local file
    # system or in Git repo
    # Use 'workflow_params' or file in Git repo to generate YAML file

    # Set regular expression for finding workflow files on git repositories
    # Assumptions:
    # - A URL needs to consist of a root, a "separator" keyword, a
    #   branch/commit, and a "file path", separated by slashes
    # - The root is the part of the URL up to the separator and is assumed to
    #   represent the "git clone URL" when '.git' is appended
    # - Accepted separator keywords are 'blob', 'src' and 'tree'
    # - The value branch/commit is used to checkout the repo to that state
    #   before obtaining the file
    # - The "file path" segment represents the relative path to the CWL
    #   workflow file when inside the repo
    #
    # All of the above assumptions should be met when copying the links of
    # files in most repos on GitHub, GitLab or Bitbucket
    #
    # Note that the "file path" portion (see above) of a CWL *parameter file*
    # can be *optionally* appended to the URL
    #
    # The following additional rules apply for workflow and/or parameter files:
    # - CWL workflow files *must* end in .cwl, .yml, .yaml or .json
    # - Parameter files *must* end in '.yml', '.yaml' or '.json'
    # - Accepted delimiters for separating workflow and parameter file, if
    #   specified, are: ',', ';', ':', '|'
    re_git_file = re.compile(
        (
            r'^(https?:.*)\/(blob|src|tree)\/(.*?)\/(.*?\.(cwl|yml|yaml|json))'
            r'[,:;|]?(.*\.(yml|yaml|json))?'
        )
    )

    # Create directory for storing workflow files
    workflow_dir = os.path.abspath(
        os.path.join(
            data['internal']['out_dir'], 'workflow_files'
        )
    )
    try:
        os.mkdir(workflow_dir)

    except OSError:
        # TODO: Do something more reasonable here
        pass

    # Get main workflow file
    user_string = data['api']['request']['workflow_url']
    m = re_git_file.match(user_string)

    # Get workflow from Git repo if regex matches
    if m:

        repo_url = '.'.join([m.group(1), 'git'])
        branch_commit = m.group(3)
        cwl_path = m.group(4)

        # Try to clone repo
        if not subprocess.run(
            [
                'git',
                'clone',
                repo_url,
                os.path.join(workflow_dir, 'repo')
            ],
            check=True
        ):
            logger.error(
                (
                    'Could not clone Git repository. Check value of '
                    "'workflow_url' in run request."
                )
            )
            raise BadRequest

        # Try to checkout branch/commit
        if not subprocess.run(
            [
                'git',
                '--git-dir',
                os.path.join(workflow_dir, 'repo', '.git'),
                '--work-tree',
                os.path.join(workflow_dir, 'repo'),
                'checkout',
                branch_commit
            ],
            check=True
        ):
            logger.error(
                (
                    'Could not checkout repository commit/branch. Check value '
                    "of 'workflow_url' in run request."
                )
            )
            raise BadRequest

        # Set CWL path
        data['internal']['cwl_path'] = os.path.join(
            workflow_dir,
            'repo',
            cwl_path
        )

    # Else assume value of 'workflow_url' represents file on local file system
    else:

        # Set main CWL workflow file path
        data['internal']['cwl_path'] = os.path.abspath(
            data['api']['request']['workflow_url']
        )

    # Extract name and extensions of workflow
    workflow_name_ext = os.path.splitext(
        os.path.basename(
            data['internal']['cwl_path']
        )
    )

    # Try to get parameters from 'workflow_params' field
    if data['api']['request']['workflow_params']:
        data['internal']['param_file_path'] = os.path.join(
            workflow_dir,
            '.'.join([
                str(workflow_name_ext[0]),
                'yml',
            ]),
        )
        with open(data['internal']['param_file_path'], 'w') as yaml_file:
            dump(
                data['api']['request']['workflow_params'],
                yaml_file,
                allow_unicode=True,
                default_flow_style=False
            )

    # Or from provided relative file path in repo
    elif m and m.group(6):
        param_path = m.group(6)
        data['internal']['param_file_path'] = os.path.join(
            workflow_dir,
            'repo',
            param_path,
        )

    # Else try to see if there is a 'yml', 'yaml' or 'json' file with exactly
    # the same basename as CWL in same dir
    else:
        param_file_extensions = ['yml', 'yaml', 'json']
        for ext in param_file_extensions:
            possible_param_file = os.path.join(
                workflow_dir,
                'repo',
                '.'.join([
                    str(workflow_name_ext[0]),
                    ext,
                ]),
            )
            if os.path.isfile(possible_param_file):
                data['internal']['param_file_path'] = possible_param_file
                break

    # Raise BadRequest if not parameter file was found
    if 'param_file_path' not in data['internal']:
        raise BadRequest

    # Extract workflow attachments from form data dictionary
    if 'workflow_attachment' in data['api']['request']:

        # TODO: do something with data['workflow_attachment']

        # Strip workflow attachments from data
        del data['api']['request']['workflow_attachment']
    
    # Add workflow base name (without extension) to document
    data['api']['run_log']['name'] = str(workflow_name_ext[0])

    # Return form data stripped of workflow attachments
    return data


def __run_workflow(
    config: Dict,
    document: Dict,
    **kwargs
) -> None:
    """Helper function `run_workflow()`."""
    tes_url = get_conf(config, 'tes', 'url')
    remote_storage_url = get_conf(config, 'storage', 'remote_storage_url')
    run_id = document['run_id']
    task_id = document['task_id']
    tmp_dir = document['internal']['tmp_dir']
    cwl_path = document['internal']['cwl_path']
    param_file_path = document['internal']['param_file_path']

    # Build command
    command_list = [
        'cwl-tes',
        '--debug',
        '--leave-outputs',
        '--remote-storage-url', remote_storage_url,
        '--tes', tes_url,
        cwl_path,
        param_file_path
    ]

    # Add authorization parameters
    if 'token' in kwargs:
        auth_params = [
            '--token-public-key', get_conf(
                config,
                'security',
                'jwt',
                'public_key'
            ).encode('unicode_escape').decode('utf-8'),
            '--token', kwargs['token'],
        ]
        command_list[2:2] = auth_params

    # TEST CASE FOR SYSTEM ERROR
    # command_list = [
    #     '/path/to/non_existing/script',
    # ]
    # TEST CASE FOR EXECUTOR ERROR
    # command_list = [
    #     '/bin/false',
    # ]
    # TEST CASE FOR SLOW COMPLETION WITH ARGUMENT (NO STDOUT/STDERR)
    # command_list = [
    #     'sleep',
    #     '30',
    # ]

    # Get timeout duration
    timeout_duration = get_conf(
        config,
        'api',
        'endpoint_params',
        'timeout_run_workflow',
    )

    # Execute command as background task
    logger.info(
        (
            "Starting execution of run '{run_id}' as task '{task_id}' in "
            "'{tmp_dir}'..."
        ).format(
            run_id=run_id,
            task_id=task_id,
            tmp_dir=tmp_dir,
        )
    )
    task__run_workflow.apply_async(
        None,
        {
            'command_list': command_list,
            'tmp_dir': tmp_dir,
        },
        task_id=task_id,
        soft_time_limit=timeout_duration,
    )
    return None
