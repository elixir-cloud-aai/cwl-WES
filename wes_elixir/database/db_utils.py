"""Utility functions for MongoDB document insertion, updates and retrieval."""

from typing import (Any, Mapping, Optional)

from bson.objectid import ObjectId
from pymongo.collection import ReturnDocument
from pymongo import collection as Collection


def find_one_latest(collection: Collection) -> Optional[Mapping[Any, Any]]:
    """Returns newest/latest object, stripped of the object id, or None if no
    object exists: collection.
    """
    try:
        return collection.find(
            {},
            {'_id': False}
        ).sort([('_id', -1)]).limit(1).next()
    except StopIteration:
        return None


def find_id_latest(collection: Collection) -> Optional[ObjectId]:
    """Returns object id of newest/latest object, or None if no object exists.
    """
    try:
        return collection.find().sort([('_id', -1)]).limit(1).next()['_id']
    except StopIteration:
        return None


def update_run_state(
    collection: Collection,
    task_id: str,
    state: str = 'UNKNOWN'
) -> Optional[Mapping[Any, Any]]:
    """Updates state of workflow run and returns document."""
    return collection.find_one_and_update(
        {'task_id': task_id},
        {'$set': {'api.state': state}},
        return_document=ReturnDocument.AFTER
    )


def upsert_fields_in_root_object(
    collection: Collection,
    task_id: str,
    root: str,
    **kwargs
) -> Optional[Mapping[Any, Any]]:
    """Inserts (or updates) fields in(to) the same root (object) field and
    returns document.
    """
    return collection.find_one_and_update(
        {'task_id': task_id},
        {'$set': {
            '.'.join([root, key]):
                value for (key, value) in kwargs.items()
        }},
        return_document=ReturnDocument.AFTER
    )


def update_tes_task_state(
    collection: Collection,
    task_id: str,
    tes_id: str,
    state: str
) -> Optional[Mapping[Any, Any]]:
    """Updates `state` field in TES task log and returns updated document."""
    return collection.find_one_and_update(
        {'task_id': task_id, 'api.task_logs': {'$elemMatch': {'id': tes_id}}},
        {'$set': {'api.task_logs.$.state': state}},
        return_document=ReturnDocument.AFTER
    )


def append_to_tes_task_logs(
    collection: Collection,
    task_id: str,
    tes_log: str
) -> Optional[Mapping[Any, Any]]:
    """Appends task log to TES task logs and returns updated document."""
    return collection.find_one_and_update(
        {'task_id': task_id},
        {'$push': {'api.task_logs': tes_log}},
        return_document=ReturnDocument.AFTER
    )
