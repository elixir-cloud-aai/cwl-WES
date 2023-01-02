"""Controller for GA4GH WES API endpoints."""

import logging
from typing import Dict, Optional

from bson.objectid import ObjectId
from celery import uuid
from connexion import request
from flask import current_app
from pymongo.collection import Collection

from foca.utils.logging import log_traffic

from cwl_wes.ga4gh.wes.endpoints.run_workflow import run_workflow
from cwl_wes.ga4gh.wes.endpoints.service_info import ServiceInfo
from cwl_wes.ga4gh.wes.states import States
from cwl_wes.tasks.cancel_run import task__cancel_run
from cwl_wes.utils.controllers import get_document_if_allowed

# pragma pylint: disable=invalid-name,unused-argument

# Get logger instance
logger = logging.getLogger(__name__)


# GET /runs/<run_id>
@log_traffic
def GetRunLog(run_id, *args, **kwargs) -> Dict:
    """Get detailed run info.

    Returns:
        Run info object.
    """
    document = get_document_if_allowed(
        config=current_app.config,
        run_id=run_id,
        projection={
            "user_id": True,
            "api": True,
            "_id": False,
        },
        user_id=kwargs.get("user_id"),
    )
    assert "api" in document, "'api' key not in document"
    return document["api"]


# POST /runs/<run_id>/cancel
@log_traffic
def CancelRun(run_id, *args, **kwargs) -> Dict:
    """Cancel unfinished workflow run.

    Returns:
        Run identifier object.
    """
    document = get_document_if_allowed(
        config=current_app.config,
        run_id=run_id,
        projection={
            "user_id": True,
            "task_id": True,
            "api.state": True,
            "_id": False,
        },
        user_id=kwargs.get("user_id"),
    )
    assert "api" in document, "'api' key not in document"
    assert "state" in document["api"], "'state' key not in document['api']"

    if document["api"]["state"] in States.CANCELABLE:
        timeout_duration = (
            current_app.config.foca.custom.controller.timeout_cancel_run
        )
        task_id = uuid()
        logger.info(f"Canceling run '{run_id}' as background task: {task_id}")
        task__cancel_run.apply_async(
            None,
            {
                "run_id": run_id,
                "task_id": document["task_id"],
                "token": kwargs.get("jwt"),
            },
            task_id=task_id,
            soft_time_limit=timeout_duration,
        )

    return {"run_id": run_id}


# GET /runs/<run_id>/status
@log_traffic
def GetRunStatus(run_id, *args, **kwargs) -> Dict:
    """Get run status.

    Returns:
        Run status object.
    """
    document = get_document_if_allowed(
        config=current_app.config,
        run_id=run_id,
        projection={
            "user_id": True,
            "api.state": True,
            "_id": False,
        },
        user_id=kwargs.get("user_id"),
    )
    assert "api" in document, "'api' key not in document"
    assert "state" in document["api"], "'state' key not in document['api']"
    return {"run_id": run_id, "state": document["api"]["state"]}


# GET /service-info
@log_traffic
def GetServiceInfo(*args, **kwargs) -> Optional[Dict]:
    """Get service info.

    Returns:
        Service info object.
    """
    service_info = ServiceInfo()
    return service_info.get_service_info()


# GET /runs
@log_traffic
def ListRuns(*args, **kwargs) -> Dict:
    """List IDs and status of all workflow runs.

    Returns:
        Run list object.
    """
    collection_runs: Collection = (
        current_app.config.foca.db.dbs["cwl-wes-db"].collections["runs"].client
    )
    page_size = kwargs.get(
        "page_size",
        current_app.config.foca.custom.controller.default_page_size,
    )
    page_token = kwargs.get("page_token", "")

    filter_dict = {}
    if "user_id" in kwargs:
        filter_dict["user_id"] = kwargs["user_id"]
    if page_token != "":
        filter_dict["_id"] = {"$lt": ObjectId(page_token)}
    cursor = (
        collection_runs.find(
            filter=filter_dict,
            projection={
                "run_id": True,
                "api.state": True,
            },
        )
        .sort("_id", -1)
        .limit(page_size)
    )
    runs_list = list(cursor)

    if runs_list:
        next_page_token = str(runs_list[-1]["_id"])
    else:
        next_page_token = ""

    for run in runs_list:
        del run["_id"]
        run["state"] = run["api"]["state"]
        del run["api"]

    return {"next_page_token": next_page_token, "runs": runs_list}


# POST /runs
@log_traffic
def RunWorkflow(*args, **kwargs) -> Dict:
    """Trigger workflow run.

    Returns:
        Run identifier object.
    """
    response = run_workflow(
        config=current_app.config,
        form_data=request.form,
        *args,
        **kwargs,
    )
    return response
