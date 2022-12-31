"""Utility functions for database access."""

import logging
from typing import Any, List, Mapping, Optional

from bson.objectid import ObjectId
from pymongo import collection as Collection
from pymongo.collection import ReturnDocument

# Get logger instance
logger = logging.getLogger(__name__)


def update_run_state(
    collection: Collection, task_id: str, state: str = "UNKNOWN"
) -> Optional[Mapping[Any, Any]]:
    """Updates state of workflow run and returns document."""
    return collection.find_one_and_update(
        {"task_id": task_id},
        {"$set": {"api.state": state}},
        return_document=ReturnDocument.AFTER,
    )


def upsert_fields_in_root_object(
    collection: Collection, task_id: str, root: str, **kwargs
) -> Optional[Mapping[Any, Any]]:
    """Inserts (or updates) fields in(to) the same root (object) field and
    returns document.
    """
    return collection.find_one_and_update(
        {"task_id": task_id},
        {
            "$set": {
                ".".join([root, key]): value for (key, value) in kwargs.items()
            }
        },
        return_document=ReturnDocument.AFTER,
    )


def update_tes_task_state(
    collection: Collection, task_id: str, tes_id: str, state: str
) -> Optional[Mapping[Any, Any]]:
    """Updates `state` field in TES task log and returns updated document."""
    return collection.find_one_and_update(
        {"task_id": task_id, "api.task_logs": {"$elemMatch": {"id": tes_id}}},
        {"$set": {"api.task_logs.$.state": state}},
        return_document=ReturnDocument.AFTER,
    )


def append_to_tes_task_logs(
    collection: Collection,
    task_id: str,
    tes_log: Mapping,
) -> Optional[Mapping[Any, Any]]:
    """Appends task log to TES task logs and returns updated document."""
    return collection.find_one_and_update(
        {"task_id": task_id},
        {"$push": {"api.task_logs": tes_log}},
        return_document=ReturnDocument.AFTER,
    )


def find_tes_task_ids(collection: Collection, run_id: str) -> List:
    """Get list of TES task ids associated with a run of interest."""
    return collection.distinct("api.task_logs.id", {"run_id": run_id})


def set_run_state(
    collection: Collection,
    run_id: str,
    task_id: Optional[str] = None,
    state: str = "UNKNOWN",
):
    """Set/update state of run associated with Celery task."""
    if not task_id:
        document = collection.find_one(
            filter={"run_id": run_id},
            projection={
                "task_id": True,
                "_id": False,
            },
        )
        _task_id = document["task_id"]
    else:
        _task_id = task_id
    try:
        document = update_run_state(
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


def find_one_latest(collection: Collection) -> Optional[Mapping[Any, Any]]:
    """Returns newest object, stripped of the object id, or None if no object
    exists.
    """
    try:
        return (
            collection.find({}, {"_id": False})
            .sort([("_id", -1)])
            .limit(1)
            .next()
        )
    except StopIteration:
        return None


def find_id_latest(collection: Collection) -> Optional[ObjectId]:
    """Returns object id of newest object, or None if no object exists."""
    try:
        return collection.find().sort([("_id", -1)]).limit(1).next()["_id"]
    except StopIteration:
        return None
