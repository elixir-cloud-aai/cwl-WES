"""Controller for GA4GH WES API endpoints."""

import logging

from celery import current_app as celery_app
from connexion import request
from flask import current_app

import wes_elixir.ga4gh.wes.utils_runs as runs
import wes_elixir.ga4gh.wes.utils_service_info as service_info
from wes_elixir.security.decorators import auth_token_optional


# Get logger instance
logger = logging.getLogger(__name__)


# GET /runs/<run_id>
@auth_token_optional
def GetRunLog(run_id, *args, **kwargs):
    """Returns detailed run info."""
    response = runs.get_run_log(
        config=current_app.config,
        run_id=run_id,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# POST /runs/<run_id>/cancel
@auth_token_optional
def CancelRun(run_id, *args, **kwargs):
    """Cancels unfinished workflow run."""
    response = runs.cancel_run(
        config=current_app.config,
        celery_app=celery_app,
        run_id=run_id,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# GET /runs/<run_id>/status
@auth_token_optional
def GetRunStatus(run_id, *args, **kwargs):
    """Returns run status."""
    response = runs.get_run_status(
        config=current_app.config,
        run_id=run_id,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# GET /service-info
@auth_token_optional
def GetServiceInfo(*args, **kwargs):
    """Returns service info."""
    response = service_info.get_service_info(
        config=current_app.config,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# GET /runs
@auth_token_optional
def ListRuns(*args, **kwargs):
    """Lists IDs and status of all workflow runs."""
    response = runs.list_runs(
        config=current_app.config,
        *args,
        **kwargs
    )
    log_request(request, response)
    return response


# POST /runs
@auth_token_optional
def RunWorkflow(*args, **kwargs):
    """Executes workflow."""
    response = runs.run_workflow(
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
