from bson.objectid import ObjectId
from pymongo.collection import ReturnDocument


def find_one_latest(collection):
    '''Returns newest/latest object, stripped of the object id, or None if no object exists'''
    try:
        return collection.find({}, {'_id': False}).sort([('_id', -1)]).limit(1).next()
    except StopIteration:
        return None


def find_id_latest(collection):
    '''Returns object id of newest/latest object, or None if no object exists'''
    try:
        return collection.find().sort([('_id', -1)]).limit(1).next()['_id']
    except StopIteration:
        return None


def update_run_state(
    collection,
    task_id,
    state="UNKNOWN"
):
    '''Update state of workflow run'''
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
    '''Insert (or update) fields in(to) the same root (object) field'''
    return collection.find_one_and_update(
        {"task_id": task_id},
        {"$set": {".".join([root, key]):value for (key,value) in kwargs.items()}},
        return_document=ReturnDocument.AFTER
    )