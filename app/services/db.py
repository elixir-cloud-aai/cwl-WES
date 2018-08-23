from bson.objectid import ObjectId


class PyMongoUtils:
    '''Utility functions for PyMongo'''

    def find_one_by_id(collection, object_id):
        '''Returns single object by object id, stripped of object id, or None if object not found'''
        return collection.find_one({'_id': ObjectId(object_id)}, {'_id': False})


    def find_one_by_index(collection, index, value):
        '''Returns single object by index field value, stripped of object id, or None if object not found'''
        return collection.find_one({index: value}, {'_id': False})


    def find_one_field_by_index(collection, index, value, select):
        '''Returns single field from single object by index field value, stripped of object id, or None if object not found'''
        return collection.find_one({index: value}, {select: True, '_id': False})[select]


    def find_fields(collection, projection):
        '''Returns selected fields from all objects, stripped of object id, or None if no objects found'''
        projection_dict = {key:True for key in projection}
        projection_dict['_id'] = False
        return collection.find({}, projection_dict)


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
