"""Controller for auxiliary WES-ELIXIR API endpoints."""

import logging

from celery import current_app as celery_app
from connexion import request
from flask import current_app

from wes_elixir.security.decorators import auth_token_optional

# Get logger instance
logger = logging.getLogger(__name__)


# GET /stdout/<run_id>
@auth_token_optional
def get_stdout(run_id, *args, **kwargs):
    """Returns run STDOUT as plain text."""
    response = ""
    log_request(request, response)
    return response


# POST /stderr/<run_id>
@auth_token_optional
def get_stderr(run_id, *args, **kwargs):
    """Returns run STDERR as plain text."""
    response = ""
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
