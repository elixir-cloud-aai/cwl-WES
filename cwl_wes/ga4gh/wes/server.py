"""Controller for GA4GH WES API endpoints."""

import logging

from celery import current_app as celery_app
from connexion import request
from flask import current_app

from foca.utils.logging import log_traffic

from cwl_wes.ga4gh.wes.endpoints.cancel_run import cancel_run
from cwl_wes.ga4gh.wes.endpoints.get_run_log import get_run_log
from cwl_wes.ga4gh.wes.endpoints.get_run_status import get_run_status
from cwl_wes.ga4gh.wes.endpoints.list_runs import list_runs
from cwl_wes.ga4gh.wes.endpoints.run_workflow import run_workflow
from cwl_wes.ga4gh.wes.endpoints.get_service_info import get_service_info


# Get logger instance
logger = logging.getLogger(__name__)


# GET /runs/<run_id>
@log_traffic
def GetRunLog(run_id, *args, **kwargs):
    """Returns detailed run info."""
    response = get_run_log(
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
    response = cancel_run(
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
    response = get_run_status(
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
    response = get_service_info(
        config=current_app.config,
        *args,
        **kwargs
    )
    return response


# GET /runs
@log_traffic
def ListRuns(*args, **kwargs):
    """Lists IDs and status of all workflow runs."""
    response = list_runs(
        config=current_app.config,
        *args,
        **kwargs
    )
    return response


# POST /runs
@log_traffic
def RunWorkflow(*args, **kwargs):
    """Executes workflow."""
    response = run_workflow(
        config=current_app.config,
        form_data=request.form,
        *args,
        **kwargs
    )
    return response
