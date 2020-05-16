"""Controller for GA4GH WES API endpoints."""

import logging

from celery import current_app as celery_app
from connexion import request
from flask import current_app

import cwl_wes.ga4gh.wes.endpoints.cancel_run as cancel_run
import cwl_wes.ga4gh.wes.endpoints.get_run_log as get_run_log
import cwl_wes.ga4gh.wes.endpoints.get_run_status as get_run_status
import cwl_wes.ga4gh.wes.endpoints.list_runs as list_runs
import cwl_wes.ga4gh.wes.endpoints.run_workflow as run_workflow
import cwl_wes.ga4gh.wes.endpoints.get_service_info as get_service_info
from foca.security.decorators import param_pass


# Get logger instance
logger = logging.getLogger(__name__)


# GET /runs/<run_id>
@param_pass(current_app)
def GetRunLog(run_id, *args, **kwargs):
    """Returns detailed run info."""
    response = get_run_log.get_run_log(
        config=current_app.config,
        run_id=run_id,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# POST /runs/<run_id>/cancel
@param_pass(current_app)
def CancelRun(run_id, *args, **kwargs):
    """Cancels unfinished workflow run."""
    response = cancel_run.cancel_run(
        config=current_app.config,
        celery_app=celery_app,
        run_id=run_id,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# GET /runs/<run_id>/status
@param_pass(current_app)
def GetRunStatus(run_id, *args, **kwargs):
    """Returns run status."""
    response = get_run_status.get_run_status(
        config=current_app.config,
        run_id=run_id,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# GET /service-info
def GetServiceInfo(*args, **kwargs):
    """Returns service info."""
    response = get_service_info.get_service_info(
        config=current_app.config,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# GET /runs
@param_pass(current_app)
def ListRuns(*args, **kwargs):
    """Lists IDs and status of all workflow runs."""
    response = list_runs.list_runs(
        config=current_app.config,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# POST /runs
@param_pass(current_app)
def RunWorkflow(*args, **kwargs):
    """Executes workflow."""
    response = run_workflow.run_workflow(
        config=current_app.config,
        form_data=request.form,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


def log_request(request, response):
    """Writes request and response to log."""
    # TODO: write decorator for request logging
    logger.debug(
        (
            "Response to request \"{method} {path} {protocol}\" from "
            "{remote_addr}: {response}"
        ).format(
            method=request.environ['REQUEST_METHOD'],
            path=request.environ['PATH_INFO'],
            protocol=request.environ['SERVER_PROTOCOL'],
            remote_addr=request.environ['REMOTE_ADDR'],
            response=response,
        )
    )
