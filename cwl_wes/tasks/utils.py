"""Utility functions for Celery background tasks."""

import logging
from typing import Optional

from pymongo import collection as Collection

import cwl_wes.database.db_utils as db_utils


# Get logger instance
logger = logging.getLogger(__name__)


def set_run_state(
    collection: Collection,
    run_id: str,
    task_id: Optional[str] = None,
    state: str = 'UNKNOWN',
):
    """Set/update state of run associated with Celery task."""
    if not task_id:
        document = collection.find_one(
            filter={'run_id': run_id},
            projection={
                'task_id': True,
                '_id': False,
            }
        )
        _task_id = document['task_id']
    else:
        _task_id = task_id
    try:
        document = db_utils.update_run_state(
            collection=collection,
            task_id=_task_id,
            state=state,
        )
    except Exception as e:
        logger.exception(
            (
                "Database error. Could not update state of run '{run_id}' "
                "(task id: '{task_id}') to state '{state}'. Original error "
                "message: {type}: {msg}"
            ).format(
                run_id=run_id,
                task_id=_task_id,
                state=state,
                type=type(e).__name__,
                msg=e,
            )
        )
    finally:
        if document:
            logger.info(
                (
                    "State of run '{run_id}' (task id: '{task_id}') "
                    "changed to '{state}'."
                ).format(
                    run_id=run_id,
                    task_id=_task_id,
                    state=state,
                )
            )
