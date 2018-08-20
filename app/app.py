from connexion import App
from flask_cors import CORS
from flask_pymongo import PyMongo


# Set parameters
HOST = 'localhost'
PORT = 8888
DEBUG = True
OPENAPI_PATH = 'openapi'
OPENAPI_FILE = 'ga4gh.wes.0.3.0.openapi.yaml'


# Initialize app
app = App(
    __name__,
    specification_dir=OPENAPI_PATH,
    swagger_ui=True,
    swagger_json=True
)
app.app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
mongo = PyMongo(app.app)


def configure_app(app):
    '''Configure app'''

    # Add settings
    app = add_settings(app)

    # Apply CORS
    app.app = apply_cors(app.app)

    # Add OpenAPIs
    app = add_openapis(app)

    return app


def add_settings(app):
    '''Add settings to Flask app instance'''
    app.host = HOST
    app.port = PORT
    app.debug = DEBUG

    return(app)


def apply_cors(app):
    '''Apply cross-origin resource sharing to Flask app instance'''
    CORS(app)

    return(app)


def add_openapis(app):
    '''Add OpenAPI specifications to connexion app instance'''
    app.add_api(
        OPENAPI_FILE,
        validate_responses=True,
    )

    return(app)


def main(app):
    '''Initialize, configure and run server'''
    app = configure_app(app)
    app.run()


if __name__ == '__main__':
    main(app)
