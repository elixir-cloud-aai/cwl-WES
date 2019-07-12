"""Function for Registering MongoDB with a Flask app instance."""

import os

import logging
from typing import Dict

from flask import Flask
from flask_pymongo import ASCENDING, PyMongo

from wes_elixir.config.config_parser import get_conf
from wes_elixir.ga4gh.wes.endpoints.get_service_info import get_service_info


# Get logger instance
logger = logging.getLogger(__name__)


def register_mongodb(app: Flask) -> Flask:
    """Instantiates database and initializes collections."""
    config = app.config

    # Instantiante PyMongo client
    mongo = create_mongo_client(
        app=app,
        config=config,
    )

    # Add database
    db = mongo.db[os.environ.get('MONGO_DBNAME', get_conf(config, 'database', 'name'))]

    # Add database collection for '/service-info'
    collection_service_info = mongo.db['service-info']
    logger.debug("Added database collection 'service_info'.")

    # Add database collection for '/runs'
    collection_runs = mongo.db['runs']
    collection_runs.create_index([
            ('run_id', ASCENDING),
            ('task_id', ASCENDING),
        ],
        unique=True,
        sparse=True
    )
    logger.debug("Added database collection 'runs'.")

    # Add database and collections to app config
    config['database']['database'] = db
    config['database']['collections'] = dict()
    config['database']['collections']['runs'] = collection_runs
    config['database']['collections']['service_info'] = collection_service_info
    app.config = config

    # Initialize service info
    logger.debug('Initializing service info...')
    get_service_info(config, silent=True)

    return app


def create_mongo_client(
    app: Flask,
    config: Dict,
):
    """Register MongoDB uri and credentials."""
    if os.environ.get('MONGO_USERNAME') != '':
        auth = '{username}:{password}@'.format(
            username=os.environ.get('MONGO_USERNAME'),
            password=os.environ.get('MONGO_PASSWORD'),
        )
    else:
        auth = ''

    app.config['MONGO_URI'] = 'mongodb://{auth}{host}:{port}/{dbname}'.format(
        host=os.environ.get('MONGO_HOST', get_conf(config, 'database', 'host')),
        port=os.environ.get('MONGO_PORT', get_conf(config, 'database', 'port')),
        dbname=os.environ.get('MONGO_DBNAME', get_conf(config, 'database', 'name')),
        auth=auth
    )

    """Instantiate MongoDB client."""
    mongo = PyMongo(app)
    logger.info(
        (
            "Registered database '{name}' at URI '{uri}':'{port}' with Flask "
            'application.'
        ).format(
            name= os.environ.get('MONGO_DBNAME', get_conf(config, 'database', 'name')),
            uri=os.environ.get('MONGO_HOST', get_conf(config, 'database', 'host')),
            port=os.environ.get('MONGO_PORT', get_conf(config, 'database', 'port'))
        )
    )
    return mongo
