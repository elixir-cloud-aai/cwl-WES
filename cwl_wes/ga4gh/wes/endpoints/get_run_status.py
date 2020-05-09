"""Utility function for GET /runs/{run_id}/status endpoint."""

from connexion.exceptions import Forbidden
import logging

from typing import Dict

from foca.config.config_parser import get_conf
from cwl_wes.errors.errors import WorkflowNotFound


# Get logger instance
logger = logging.getLogger(__name__)


# Utility function for endpoint GET /runs/<run_id>/status
def get_run_status(
    config: Dict,
    run_id: str,
    *args,
    **kwargs
) -> Dict:
    """Gets status information for specific run."""
    collection_runs = get_conf(config, 'database', 'collections', 'runs')
    document = collection_runs.find_one(
        filter={'run_id': run_id},
        projection={
            'user_id': True,
            'api.state': True,
            '_id': False,
        }
    )

    # Raise error if workflow run was not found or has no task ID
    if document:
        state = document['api']['state']
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

    response = {
        'run_id': run_id,
        'state': state
    }
    return response
