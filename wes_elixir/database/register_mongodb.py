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
    db_runs = mongo.db['runs']
    db_runs.create_index([('run_id', ASCENDING)], unique=True)

    # Add database collection for '/service-info'
    db_service_info = mongo.db['service-info']
    
    # Add database and collections to app config
    app.app.config['db'] = db
    app.app.config['db_runs'] = db_runs
    app.app.config['db_service_info'] = db_service_info

    # Initialize service info    
    get_service_info(app.app.config, silent=True)

    # Return database and collections
    return app