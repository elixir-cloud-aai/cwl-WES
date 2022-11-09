"""Controller for GA4GH WES API endpoints."""

import logging

from celery import current_app as celery_app
from connexion import request
from flask import current_app

from foca.utils.logging import log_traffic

import cwl_wes.ga4gh.wes.endpoints.cancel_run as cancel_run
import cwl_wes.ga4gh.wes.endpoints.get_run_log as get_run_log
import cwl_wes.ga4gh.wes.endpoints.get_run_status as get_run_status
import cwl_wes.ga4gh.wes.endpoints.list_runs as list_runs
import cwl_wes.ga4gh.wes.endpoints.run_workflow as run_workflow
import cwl_wes.ga4gh.wes.endpoints.get_service_info as get_service_info


# Get logger instance
logger = logging.getLogger(__name__)


# GET /runs/<run_id>
@log_traffic
def GetRunLog(run_id, *args, **kwargs):
    """Returns detailed run info."""
    response = get_run_log.get_run_log(
        config=current_app.config,
        run_id=run_id,
        *args,
        **kwargs
    )
    return response


# POST /runs/<run_id>/cancel
@log_traffic
def CancelRun(run_id, *args, **kwargs):
    """Cancels unfinished workflow run."""
    response = cancel_run.cancel_run(
        config=current_app.config,
        celery_app=celery_app,
        run_id=run_id,
        *args,
        **kwargs
    )
    return response


# GET /runs/<run_id>/status
@log_traffic
def GetRunStatus(run_id, *args, **kwargs):
    """Returns run status."""
    response = get_run_status.get_run_status(
        config=current_app.config,
        run_id=run_id,
        *args,
        **kwargs
    )
    return response


# GET /service-info
@log_traffic
def GetServiceInfo(*args, **kwargs):
    """Returns service info."""
    response = get_service_info.get_service_info(
        config=current_app.config,
        *args,
        **kwargs
    )
    return response


# GET /runs
@log_traffic
def ListRuns(*args, **kwargs):
    """Lists IDs and status of all workflow runs."""
    response = list_runs.list_runs(
        config=current_app.config,
        *args,
        **kwargs
    )
    return response


# POST /runs
@log_traffic
def RunWorkflow(*args, **kwargs):
    """Executes workflow."""
    response = run_workflow.run_workflow(
        config=current_app.config,
        form_data=request.form,
        *args,
        **kwargs
    )
    return response
