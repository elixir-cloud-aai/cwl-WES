from copy import deepcopy
from datetime import datetime
import logging

import wes_elixir.database.db_utils as db_utils


# Get logger instance
logger = logging.getLogger(__name__)


# Helper function GET /service-info
def get_service_info(config, silent=False, *args, **kwargs):
    '''Returns readily formatted service info or None (in silent mode);
    creates service info database document if does not exist'''

    # Re-assign config values
    collection_service_info = config['database']['collections']['service_info']
    collection_runs = config['database']['collections']['runs']
    service_info = deepcopy(config['service_info'])

    # Write current service info to database if absent or different from latest
    if not service_info == db_utils.find_one_latest(collection_service_info):
        collection_service_info.insert(service_info)
        logger.info("Updated service info: {service_info}".format(
            service_info=service_info,
        ))
    else:
        logger.debug("No change in service info. Not updated.")

    # Return None when called in silent mode:
    if silent:
        return None

    # Add current system state counts
    service_info['system_state_counts'] = __get_system_state_counts(
        collection_runs
    )

    # Add timestamps
    service_info['tags']['timestamp_last_service_info_update'] = \
        db_utils.find_id_latest(collection_service_info).generation_time
    service_info['tags']['timestamp_current'] = datetime.utcnow().isoformat()

    # Return service info
    return service_info


def __get_system_state_counts(collection_runs):
    '''Get current system state counts'''

    # Iterate through list
    current_counts = __init_system_state_counts()

    # Query database for workflow run states
    cursor = collection_runs.find(
        filter={},
        projection={
            'api.state': True,
            '_id': False,
        }
    )

    # Iterate over states
    for record in cursor:

        # Increase counter for state of current record
        current_counts[record['api']['state']] += 1

    # Return counts
    return(current_counts)


def __init_system_state_counts():
    '''Initialize system state counts'''

    # Set all state counts to zero
    # TODO: Get states programmatically
    return {
        "UNKNOWN": 0,
        "QUEUED": 0,
        "INITIALIZING": 0,
        "RUNNING": 0,
        "PAUSED": 0,
        "COMPLETE": 0,
        "EXECUTOR_ERROR": 0,
        "SYSTEM_ERROR": 0,
        "CANCELED": 0
    }
