"""Utility functions for GET /service-info endpoint."""

from copy import deepcopy
from datetime import datetime
import logging
from typing import Any, Dict

from flask import Config
from foca.utils.db import find_id_latest, find_one_latest
from pymongo import collection as Collection

from cwl_wes.ga4gh.wes.states import States

# pragma pylint: disable=unused-argument

# Get logger instance
logger = logging.getLogger(__name__)


# Helper function GET /service-info
def get_service_info(
    config: Config,
    *args: Any,
    silent: bool = False,
    **kwarg: Any,
):
    """Get formatted service info.

    Creates service info database document if it does not exist.

    Args:
        config: App configuration.
        *args: Variable length argument list.
        silent: Whether to return service info or `None` (in silent mode).
        **kwargs: Arbitrary keyword arguments.

    Returns:
        Readily formatted service info, or `None` (in silent mode);
    """
    collection_service_info: Collection.Collection = (
        config.foca.db.dbs["cwl-wes-db"].collections["service_info"].client
    )
    collection_runs: Collection.Collection = (
        config.foca.db.dbs["cwl-wes-db"].collections["runs"].client
    )
    service_info = deepcopy(config.foca.custom.service_info.dict())

    # Write current service info to database if absent or different from latest
    if not service_info == find_one_latest(collection_service_info):
        collection_service_info.insert(service_info)
        logger.info(f"Updated service info: {service_info}")
    else:
        logger.debug("No change in service info. Not updated.")

    # Return None when called in silent mode:
    if silent:
        return None

    # Add current system state counts
    service_info["system_state_counts"] = __get_system_state_counts(
        collection_runs
    )

    # Add timestamps
    _id = find_id_latest(collection_service_info)
    if _id:
        service_info["tags"]["last_service_info_update"] = _id.generation_time
    service_info["tags"]["current_time"] = datetime.utcnow().isoformat()

    return service_info


def __get_system_state_counts(collection: Collection) -> Dict[str, int]:
    """Get current system state counts.

    Args:
        collection: MongoDB collection object.

    Returns:
        Dictionary of counts per state.
    """
    current_counts = __init_system_state_counts()

    # Query database for workflow run states
    cursor = collection.find(
        filter={},
        projection={
            "api.state": True,
            "_id": False,
        },
    )

    # Iterate over states and increase counter
    for record in cursor:
        current_counts[record["api"]["state"]] += 1

    return current_counts


def __init_system_state_counts() -> Dict[str, int]:
    """Initialize system state counts.

    Returns:
        Dictionary of state counts, inititalized to zero.
    """
    return {state: 0 for state in States.ALL}
