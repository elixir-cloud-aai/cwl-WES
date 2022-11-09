"""Utility functions for POST /runs/{run_id}/cancel endpoints."""

import logging
from typing import Dict

from celery import (Celery, uuid)
from connexion.exceptions import Forbidden

from flask import Config

from cwl_wes.exceptions import WorkflowNotFound
from cwl_wes.ga4gh.wes.states import States
from cwl_wes.tasks.tasks.cancel_run import task__cancel_run


# Get logger instance
logger = logging.getLogger(__name__)


# Utility function for endpoint POST /runs/<run_id>/delete
def cancel_run(
    config: Config,
    celery_app: Celery,
    run_id: str,
    *args,
    **kwargs
) -> Dict:
    """Cancels running workflow."""
    foca_config = config.foca
    collection_runs = foca_config.db.dbs['cwl-wes-db'].collections['runs']
    document = collection_runs.find_one(
        filter={'run_id': run_id},
        projection={
            'user_id': True,
            'task_id': True,
            'api.state': True,
            '_id': False,
        }
    )

    # Raise error if workflow run was not found
    if not document:
        logger.error("Run '{run_id}' not found.".format(run_id=run_id))
        raise WorkflowNotFound

    # Raise error trying to access workflow run that is not owned by user
    # Only if authorization enabled
    if 'user_id' in kwargs and document['user_id'] != kwargs['user_id']:
        logger.error(
            (
                "User '{user_id}' is not allowed to access workflow run "
                "'{run_id}'."
            ).format(
                user_id=kwargs['user_id'],
                run_id=run_id,
            )
        )
        raise Forbidden

    # Cancel unfinished workflow run in background
    if document['api']['state'] in States.CANCELABLE:

        # Get timeout duration
        timeout_duration = foca_config.custom.endpoint_params.timeout_cancel_run

        # Execute cancelation task in background
        task_id = uuid()
        logger.info(
            (
                "Canceling run '{run_id}' as background task "
                "'{task_id}'..."
            ).format(
                run_id=run_id,
                task_id=task_id,
            )
        )
        task__cancel_run.apply_async(
            None,
            {
                'run_id': run_id,
                'task_id': document['task_id'],
                'token': kwargs.get('jwt'),
            },
            task_id=task_id,
            soft_time_limit=timeout_duration,
        )

    response = {'run_id': run_id}
    return response
