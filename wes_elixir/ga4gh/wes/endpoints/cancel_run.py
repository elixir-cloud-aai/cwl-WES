"""Utility functions for POST /runs/{run_id}/cancel endpoints."""

from connexion.exceptions import Forbidden
import logging

from celery import Celery
from typing import Dict

from wes_elixir.config.config_parser import get_conf
from wes_elixir.errors.errors import WorkflowNotFound
from wes_elixir.tasks.tasks.cancel_run import task__cancel_run


# Get logger instance
logger = logging.getLogger(__name__)


# Utility function for endpoint POST /runs/<run_id>/delete
def cancel_run(
    config: Dict,
    celery_app: Celery,
    run_id: str,
    *args,
    **kwargs
) -> Dict:
    """Cancels running workflow."""
    collection_runs = get_conf(config, 'database', 'collections', 'runs')
    document = collection_runs.find_one(
        filter={'run_id': run_id},
        projection={
            'user_id': True,
            'task_id': True,
            '_id': False,
        }
    )

    # Raise error if workflow run was not found or has no task ID
    if document:
        task_id = document['task_id']
    else:
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

    # Cancel workflow run
    try:
        # TODO: Work on this!!!
        # TODO: Implement this better; terminate=True should be last resort
        # TODO: See here:
        # https://stackoverflow.com/questions/8920643/cancel-an-already-executing-task-with-celery
        celery_app.control.revoke(task_id, terminate=True, signal='SIGHUP')
        task__cancel_run.apply_async()

    # Raise error if workflow run was not found
    except Exception as e:
        logger.error(
            (
                "Failed to revoked task '{task_id}' for run '{run_id}'. "
                'Possibly the workflow is not running anymore. Original '
                'error message: {type}: {msg}'
            ).format(
                task_id=task_id,
                run_id=run_id,
                type=type(e).__name__,
                msg=e,
            )
        )
        raise WorkflowNotFound

    response = {'run_id': run_id}
    return response
