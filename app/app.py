from configloader import ConfigLoader
from connexion import App
from flask_cors import CORS
from flask_pymongo import PyMongo
from pathlib import Path
import os, sys


# Parse config file
config = ConfigLoader()
if 'WES_CONFIG' not in os.environ:
    sys.exit("Environment variable 'WES_CONFIG' not set.\nExecution aborted.")
if not os.path.isfile(os.environ['WES_CONFIG']):
    sys.exit("No config file found at location specified in 'WES_CONFIG': {}.\nExecution aborted.".format(os.environ['WES_CONFIG']))
config.update_from_yaml_env('WES_CONFIG')


# Initialize app
try:
    app = App(
        __name__,
        specification_dir=config['openapi']['path'],
        swagger_ui=True,
        swagger_json=True
    )
except KeyError:
    sys.exit("Config file corrupt. Execution aborted.")

app.app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
mongo = PyMongo(app.app)


def configure_app(app):
    '''Configure app'''

    # Add settings
    app = add_settings(app)

    # Apply CORS
    app.app = apply_cors(app.app)

    # Add OpenAPIs
    app = add_openapi(app)

    return app


def add_settings(app):
    '''Add settings to Flask app instance'''
    try:
        app.host = config['server']['host']
        app.port = config['server']['port']
        app.debug = config['server']['debug']
    except KeyError:
        sys.exit("Config file corrupt. Execution aborted.")

    return(app)


def apply_cors(app):
    '''Apply cross-origin resource sharing to Flask app instance'''
    CORS(app)

    return(app)


def add_openapi(app):
    '''Add OpenAPI specification to connexion app instance'''
    try:
        app.add_api(
            config['openapi']['yaml_specs'],
            validate_responses=True,  # FIXME: This does not seem to work
        )
    except KeyError:
        sys.exit("Config file corrupt. Execution aborted.")

    return(app)


def main(app):
    '''Initialize, configure and run server'''
    app = configure_app(app)
    app.run()


if __name__ == '__main__':
    main(app)
