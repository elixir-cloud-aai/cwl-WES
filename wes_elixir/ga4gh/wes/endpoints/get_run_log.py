"""Utility function for GET /runs/{run_id} endpoint."""

from connexion.exceptions import Forbidden
import logging

from typing import Dict

from wes_elixir.config.config_parser import get_conf
from wes_elixir.errors.errors import WorkflowNotFound


# Get logger instance
logger = logging.getLogger(__name__)


# Utility function for endpoint GET /runs/<run_id>
def get_run_log(
    config: Dict,
    run_id: str,
    *args,
    **kwargs
) -> Dict:
    """Gets detailed log information for specific run."""
    collection_runs = get_conf(config, 'database', 'collections', 'runs')
    document = collection_runs.find_one(
        filter={'run_id': run_id},
        projection={
            'user_id': True,
            'api': True,
            '_id': False,
        }
    )

    # Raise error if workflow run was not found or has no task ID
    if document:
        run_log = document['api']
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

    # Remove 

    return run_log
