"""Utility functions for GET /service-info endpoint."""

from copy import deepcopy
from datetime import datetime
import logging
from typing import (Any, Dict, Mapping)

from pymongo import collection as Collection

import wes_elixir.database.db_utils as db_utils


# Get logger instance
logger = logging.getLogger(__name__)


# Helper function GET /service-info
def get_service_info(
    config: Mapping,
    silent: bool = False,
    *args: Any,
    **kwarg: Any
):
    """Returns readily formatted service info or `None` (in silent mode);
    creates service info database document if it does not exist."""
    collection_service_info = config['database']['collections']['service_info']
    collection_runs = config['database']['collections']['runs']
    service_info = deepcopy(config['service_info'])

    # Write current service info to database if absent or different from latest
    if not service_info == db_utils.find_one_latest(collection_service_info):
        collection_service_info.insert(service_info)
        logger.info('Updated service info: {service_info}'.format(
            service_info=service_info,
        ))
    else:
        logger.debug('No change in service info. Not updated.')

    # Return None when called in silent mode:
    if silent:
        return None

    # Add current system state counts
    service_info['system_state_counts'] = __get_system_state_counts(
        collection_runs
    )

    # Add timestamps
    _id = db_utils.find_id_latest(collection_service_info)
    if _id:
        service_info['tags']['last_service_info_update'] = _id.generation_time
    service_info['tags']['current_time'] = datetime.utcnow().isoformat()

    return service_info


def __get_system_state_counts(collection: Collection) -> Dict[str, int]:
    """Gets current system state counts."""
    current_counts = __init_system_state_counts()

    # Query database for workflow run states
    cursor = collection.find(
        filter={},
        projection={
            'api.state': True,
            '_id': False,
        }
    )

    # Iterate over states and increase counter
    for record in cursor:
        current_counts[record['api']['state']] += 1

    return current_counts


def __init_system_state_counts() -> Dict[str, int]:
    """Initializes system state counts."""
    # TODO: Get states programmatically or define as enum
    # Set all state counts to zero
    return {
        'UNKNOWN': 0,
        'QUEUED': 0,
        'INITIALIZING': 0,
        'RUNNING': 0,
        'PAUSED': 0,
        'COMPLETE': 0,
        'EXECUTOR_ERROR': 0,
        'SYSTEM_ERROR': 0,
        'CANCELED': 0,
        'CANCELING': 0,
    }
