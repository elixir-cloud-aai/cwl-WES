from flask_pymongo import ASCENDING, PyMongo

from wes_elixir.ga4gh.wes.utils_service_info import get_service_info


def register_mongodb(app):
    '''Instantiate database and initialize collections'''

    # Initialize PyMongo instance
    mongo = PyMongo(app.app, uri="mongodb://{host}:{port}/{name}".format(
        host=app.app.config['database']['host'],
        port=app.app.config['database']['port'],
        name=app.app.config['database']['name']
    ))

    # Add database
    db = mongo.db[app.app.config['database']['name']]

    # Add database collection for '/runs'
    collection_runs = mongo.db['runs']
    collection_runs.create_index([('run_id', ASCENDING)], unique=True)

    # Add database collection for '/service-info'
    collection_service_info = mongo.db['service-info']
    
    # Add database and collections to app config
    app.app.config['database']['database'] = db
    app.app.config['database']['collections'] = dict()
    app.app.config['database']['collections']['runs'] = collection_runs
    app.app.config['database']['collections']['service_info'] = collection_service_info

    # Initialize service info    
    get_service_info(app.app.config, silent=True)

    # Return database and collections
    return app