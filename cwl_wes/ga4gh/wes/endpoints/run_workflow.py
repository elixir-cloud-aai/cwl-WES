"""Utility functions for POST /runs endpoint."""

from json import decoder, loads
import logging
from pathlib import Path
import re
import shutil
import subprocess
from typing import Dict

from celery import uuid
from flask import Config, request
from foca.utils.misc import generate_id
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError
from yaml import dump
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename

from cwl_wes.exceptions import BadRequest
from cwl_wes.tasks.run_workflow import task__run_workflow
from cwl_wes.utils.drs import translate_drs_uris

# pragma pylint: disable=unused-argument

# Get logger instance
logger = logging.getLogger(__name__)


# Utility function for endpoint POST /runs
def run_workflow(
    config: Config, form_data: ImmutableMultiDict, *args, **kwargs
) -> Dict:
    """Execute workflow and save info to database.

    Args:
        config: Flask configuration object.
        form_data: Form data from POST /runs request.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        Unique run id.
    """
    # Validate data and prepare run environment
    form_data_dict = __immutable_multi_dict_to_nested_dict(
        multi_dict=form_data
    )
    __validate_run_workflow_request(data=form_data_dict)
    __check_service_info_compatibility(data=form_data_dict)
    document = __init_run_document(data=form_data_dict)
    document = __create_run_environment(
        config=config, document=document, **kwargs
    )

    # Start workflow run in background
    __run_workflow(config=config, document=document, **kwargs)

    response = {"run_id": document["run_id"]}
    return response


def __secure_join(basedir: Path, fname: str) -> Path:
    """Generate a secure path for a file.

    Args:
        basedir: Base directory.
        fname: Filename.

    Returns:
        Secure path.
    """
    fname = secure_filename(fname)
    if not fname:
        # Replace by a random filename
        fname = uuid()
    return basedir / fname


def __immutable_multi_dict_to_nested_dict(
    multi_dict: ImmutableMultiDict,
) -> Dict:
    """Convert ImmutableMultiDict to nested dictionary.

    Args:
        multi_dict: Immutable multi dictionary.

    Returns:
        Nested dictionary.
    """
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
    """Validate workflow run request form data.

    Set defaults for optional fields.

    Args:
        data: Workflow run request form data.
    """
    # The form data is not validated properly because all types except
    # 'workflow_attachment' are string and none are labeled as required
    # Considering the 'RunRequest' model in the specs, the following
    # assumptions are made and verified for the indicated parameters:
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

    params_required = {
        "workflow_params",
        "workflow_type",
        "workflow_type_version",
        "workflow_url",
    }
    params_str = [
        "workflow_type",
        "workflow_type_version",
        "workflow_url",
    ]
    params_dict = [
        "workflow_params",
        "workflow_engine_parameters",
        "tags",
    ]

    # Raise error if any required params are missing
    invalid = False
    for param in params_required:
        if param not in data:
            logger.error(f"Required parameter '{param}' not in request body.")
            invalid = True

    # Raise error if any string params are not of type string
    for param in params_str:
        if param in data and not isinstance(data[param], str):
            logger.error(f"Parameter '{param}' is not of string type.")
            invalid = True

    # Raise error if any dict params are not of type dict
    for param in params_dict:
        if param in data and not isinstance(data[param], dict):
            logger.error(
                f"Parameter '{param}' is not of dictionary type. Invalid JSON?"
            )
            invalid = True

    if invalid:
        logger.error("POST request does not conform to schema.")
        raise BadRequest


def __check_service_info_compatibility(data: Dict) -> None:
    """Check compatibility with service info. Not implemented."""
    # TODO: implement


def __init_run_document(data: Dict) -> Dict:
    """Initialize workflow run document.

    Args:
        data: Workflow run request form data.

    Returns:
        Workflow run document.
    """
    document: Dict = {}
    document["api"] = {}
    document["internal"] = {}
    document["api"]["request"] = data
    document["api"]["state"] = "UNKNOWN"
    document["api"]["run_log"] = {}
    document["api"]["task_logs"] = []
    document["api"]["outputs"] = {}
    return document


def __create_run_environment(config: Config, document: Dict, **kwargs) -> Dict:
    """Create run environment.

    Create unique run identifier and permanent and temporary storage
    directories for current run.

    Args:
        config: Flask configuration object.
        document: Workflow run document.
        **kwargs: Additional keyword arguments.

    Returns:
        Workflow run documument.
    """
    collection_runs: Collection = (
        config.foca.db.dbs["cwl-wes-db"].collections["runs"].client
    )
    controller_conf = config.foca.custom.controller
    info_conf = config.foca.custom.service_info
    storage_conf = config.foca.custom.storage

    # Keep on trying until a unique run id was found and inserted
    # TODO: If no more possible IDs => inf loop; fix
    while True:

        # Create unique run and task ids
        run_id = generate_id(
            charset=controller_conf.runs_id.charset,
            length=controller_conf.runs_id.length,
        )
        task_id = uuid()

        # Set temporary and output directories
        current_tmp_dir = storage_conf.tmp_dir.resolve() / run_id
        current_out_dir = storage_conf.permanent_dir.resolve() / run_id

        # Try to create workflow run directory (temporary)
        try:
            current_tmp_dir.mkdir(parents=True, exist_ok=True)
            current_out_dir.mkdir(parents=True, exist_ok=True)

        # Try new run id if directory already exists
        except FileExistsError:
            continue

        # Add run/task/user identifier, temp/output directories to document
        document["run_id"] = run_id
        document["task_id"] = task_id
        if "user_id" in kwargs:
            document["user_id"] = kwargs["user_id"]
        else:
            document["user_id"] = None
        document["internal"]["tmp_dir"] = str(current_tmp_dir)
        document["internal"]["out_dir"] = str(current_out_dir)

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
        except PyMongoError as exc:
            print("Database error")
            print(exc)
            break

        # Exit loop
        break

    # translate DRS URIs to access URLs
    translate_drs_uris(
        path=document["internal"]["workflow_files"],
        file_types=controller_conf.drs_server.file_types,
        supported_access_methods=info_conf.supported_filesystem_protocols,
        port=controller_conf.drs_server.port,
        base_path=controller_conf.drs_server.base_path,
        use_http=controller_conf.drs_server.use_http,
    )

    return document


def __process_workflow_attachments(  # pylint: disable=too-many-branches
    data: Dict,
) -> Dict:
    """Process workflow attachments.

    Args:
        data: Workflow run document.

    Returns:
        Workflow run document.
    """
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
            r"^(?P<repo_url>https?:.*)\/(blob|src|tree)\/"
            r"(?P<branch_commit>.*?)\/(?P<cwl_path>.*?\.(cwl|yml|yaml|json))"
            r"[,:;|]?(?P<params_path>.*\.(yml|yaml|json))?"
        )
    )

    # Create directory for storing workflow files
    workflow_dir = Path(data["internal"]["out_dir"]) / "workflow_files"
    data["internal"]["workflow_files"] = str(workflow_dir)
    workflow_dir.mkdir()

    # Get main workflow file
    match = re_git_file.match(data["api"]["request"]["workflow_url"])

    # Get workflow from Git repo if regex matches
    if match:

        # Try to clone repo
        if not subprocess.run(
            [
                "git",
                "clone",
                match.group("repo_url") + ".git",
                str(workflow_dir / "repo"),
            ],
            check=True,
        ):
            logger.error(
                "Could not clone Git repository. Check value of "
                "'workflow_url' in run request."
            )
            raise BadRequest

        # Try to checkout branch/commit
        if not subprocess.run(
            [
                "git",
                "--git-dir",
                str(workflow_dir / "repo" / ".git"),
                "--work-tree",
                str(workflow_dir / "repo"),
                "checkout",
                match.group("branch_commit"),
            ],
            check=True,
        ):
            logger.error(
                "Could not checkout repository commit/branch. Check value "
                "of 'workflow_url' in run request."
            )
            raise BadRequest

        # Set CWL path
        data["internal"]["cwl_path"] = str(
            workflow_dir / "repo" / match.group("cwl_path")
        )

    # Else assume value of 'workflow_url' represents file on local file system,
    # or a file that was shipped to the server as a workflow attachment.
    else:
        # Workflow attachments are grabbed directly from the Flask request
        # object rather than letting connexion parse them, since current
        # versions of connexion have a bug that prevents multiple file uploads
        # with the same name (https://github.com/zalando/connexion/issues/992).
        workflow_attachments = request.files.getlist("workflow_attachment")
        if len(workflow_attachments) > 0:
            # Save workflow attachments to workflow directory.
            for attachment in workflow_attachments:
                path = __secure_join(workflow_dir, attachment.filename)
                with open(path, "wb") as dest:
                    shutil.copyfileobj(attachment.stream, dest)

            # Adjust workflow_url to point to workflow directory.
            req_data = data["api"]["request"]
            workflow_url = __secure_join(
                workflow_dir, req_data["workflow_url"]
            )
            if workflow_url.exists():
                req_data["workflow_url"] = str(workflow_url)

        # Set main CWL workflow file path
        data["internal"]["cwl_path"] = str(
            Path(data["api"]["request"]["workflow_url"]).resolve()
        )

    # Get parameter file
    workflow_base_name = Path(data["internal"]["cwl_path"]).stem

    # Try to get parameters from 'workflow_params' field
    if data["api"]["request"]["workflow_params"]:

        # Replace `DRS URIs` in 'workflow_params'
        # replace_drs_uris(data['api']['request']['workflow_params'])

        data["internal"]["param_file_path"] = str(
            workflow_dir / f"{workflow_base_name}.yml"
        )
        with open(
            data["internal"]["param_file_path"],
            mode="w",
            encoding="utf-8",
        ) as yaml_file:
            dump(
                data["api"]["request"]["workflow_params"],
                yaml_file,
                allow_unicode=True,
                default_flow_style=False,
            )

    # Or from provided relative file path in repo
    elif match and match.group("params_path"):
        data["internal"]["param_file_path"] = str(
            workflow_dir / "repo" / match.group("params_path")
        )

    # Else try to see if there is a 'yml', 'yaml' or 'json' file with exactly
    # the same basename as CWL in same dir
    else:
        for ext in ["yml", "yaml", "json"]:
            candidate_file = (
                workflow_dir / "repo" / f"{workflow_base_name}.{ext}"
            )
            if candidate_file.is_file():
                data["internal"]["param_file_path"] = str(candidate_file)
                break

    # Raise BadRequest if no parameter file was found
    if "param_file_path" not in data["internal"]:
        raise BadRequest

    # Extract workflow attachments from form data dictionary
    if "workflow_attachment" in data["api"]["request"]:
        del data["api"]["request"]["workflow_attachment"]

    # Return form data stripped of workflow attachments
    return data


def __run_workflow(config: Config, document: Dict, **kwargs) -> None:
    """Run workflow helper function.

    Args:
        config: Flask configuration object.
        document: Workflow run document.
        **kwargs: Additional keyword arguments.

    Raises:
        BadRequest: If workflow run fails.
    """
    tes_url = config.foca.custom.controller.tes_server.url
    remote_storage_url = config.foca.custom.storage.remote_storage_url
    run_id = document["run_id"]
    task_id = document["task_id"]
    tmp_dir = document["internal"]["tmp_dir"]
    cwl_path = document["internal"]["cwl_path"]
    param_file_path = document["internal"]["param_file_path"]

    # Build command
    command_list = [
        "cwl-tes",
        "--debug",
        "--leave-outputs",
        "--remote-storage-url",
        remote_storage_url,
        "--tes",
        tes_url,
        cwl_path,
        param_file_path,
    ]

    # Add authorization parameters
    if (
        "jwt" in kwargs
        and "claims" in kwargs
        and "public_key" in kwargs["claims"]
    ):
        auth_params = [
            "--token-public-key",
            kwargs["claims"]["public_key"],
            "--token",
            kwargs["jwt"],
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
    timeout_duration = config.foca.custom.controller.timeout_run_workflow

    # Execute command as background task
    logger.info(
        f"Starting execution of run '{run_id}' as task '{task_id}' in: "
        f"{tmp_dir}"
    )
    task__run_workflow.apply_async(
        None,
        {
            "command_list": command_list,
            "tmp_dir": tmp_dir,
            "token": kwargs.get("jwt"),
        },
        task_id=task_id,
        soft_time_limit=timeout_duration,
    )
