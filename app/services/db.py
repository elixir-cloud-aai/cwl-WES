from bson.objectid import ObjectId


class PyMongoUtils:
    '''Utility functions for PyMongo'''

    def find_one_by_id(collection, object_id):
        '''Returns a single entry by object id, stripped of the object id, or None if entry was not found'''
        return collection.find_one({'_id': ObjectId(object_id)}, {'_id': False})


    def find_one_latest(collection):
        '''Returns newest/latest entry, stripped of the object id, or None if no entry exists'''
        try:
            return collection.find({}, {'_id': False}).sort([('_id', -1)]).limit(1).next()
        except StopIteration:
            return None


    def find_id_latest(collection):
        '''Returns object id of newest/latest entry, or None if no entry exists'''
        try:
            return collection.find().sort([('_id', -1)]).limit(1).next()['_id']
        except StopIteration:
            return None
