from copy import deepcopy
from datetime import datetime, timezone

import wes_elixir.database.utils as db_utils


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


def __get_system_state_counts(db_runs):
    '''Get current system state counts'''

    # Iterate through list
    current_counts = __init_system_state_counts()

    # Query database for workflow run states
    cursor = db_utils.find_fields(db_runs, ['state'])

    # Iterate over states
    for record in cursor:

        # Increase counter for state of current record
        current_counts[record['state']] += 1

    # Return counts
    return(current_counts)


def get_service_info(config, silent=False):
    '''Returns readily formatted service info or None (in silent mode); creates service info database document if does not exist'''

    # Re-assign config values
    db_service_info = config['db_service_info']
    db_runs = config['db_runs']
    service_info = deepcopy(config['service_info'])

    # Write current service info to database if absent or different from latest
    if not service_info == db_utils.find_one_latest(db_service_info):
        db_service_info.insert(service_info)

    # Return None when called in silent mode:
    if silent:
        return None

    # Add current system state counts
    service_info['system_state_counts'] = __get_system_state_counts(db_runs)

    # Add timestamps
    service_info['tags']['timestamp_last_service_info_update'] = db_utils.find_id_latest(db_service_info).generation_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
    service_info['tags']['timestamp_current'] = datetime.now().isoformat()

    # Return service info
    return service_info
