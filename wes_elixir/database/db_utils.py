"""Utility functions for MongoDB document insertion, updates and retrieval."""

from pymongo.collection import ReturnDocument


def find_one_latest(collection):
    """Returns newest/latest object, stripped of the object id, or None if no
    object exists.
    """

    try:
        return collection.find(
            {},
            {'_id': False}
        ).sort([('_id', -1)]).limit(1).next()
    except StopIteration:
        return None


def find_id_latest(collection):
    """Returns object id of newest/latest object, or None if no object exists.
    """

    try:
        return collection.find().sort([('_id', -1)]).limit(1).next()['_id']
    except StopIteration:
        return None


def update_run_state(
    collection,
    task_id,
    state="UNKNOWN"
):
    """Updates state of workflow run and returns document."""

    return collection.find_one_and_update(
        {"task_id": task_id},
        {"$set": {"api.state": state}},
        return_document=ReturnDocument.AFTER
    )


def upsert_fields_in_root_object(
    collection,
    task_id,
    root,
    **kwargs
):
    """Inserts (or updates) fields in(to) the same root (object) field and
    returns document.
    """

    return collection.find_one_and_update(
        {"task_id": task_id},
        {"$set": {
            ".".join([root, key]):
                value for (key, value) in kwargs.items()
        }},
        return_document=ReturnDocument.AFTER
    )


def update_tes_task_state(
    collection,
    task_id,
    tes_id,
    state
):
    """Updates `state` field in TES task log and returns updated document."""

    return collection.find_one_and_update(
        {"task_id": task_id, "api.task_logs": {"$elemMatch": {"id": tes_id}}},
        {"$set": {"api.task_logs.$.state": state}},
        return_document=ReturnDocument.AFTER
    )


def append_to_tes_task_logs(
    collection,
    task_id,
    tes_log
):
    """Appends task log to TES task logs and returns updated document."""

    return collection.find_one_and_update(
        {"task_id": task_id},
        {'$push': {'api.task_logs': tes_log}},
        return_document=ReturnDocument.AFTER
    )
