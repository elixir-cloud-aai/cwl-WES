from configloader import ConfigLoader
from connexion import App
from flask_cors import CORS
from flask_pymongo import PyMongo


# Parse config file
config = ConfigLoader()
config.update_from_yaml_env('WES_CONFIG')


# Initialize app
app = App(
    __name__,
    specification_dir=config['openapi']['path'],
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
    app = add_openapi(app)

    return app


def add_settings(app):
    '''Add settings to Flask app instance'''
    app.host = config['server']['host']
    app.port = config['server']['port']
    app.debug = config['server']['debug']

    return(app)


def apply_cors(app):
    '''Apply cross-origin resource sharing to Flask app instance'''
    CORS(app)

    return(app)


def add_openapi(app):
    '''Add OpenAPI specification to connexion app instance'''
    app.add_api(
        config['openapi']['yaml_specs'],
        validate_responses=True,  # FIXME: This does not seem to work
    )

    return(app)


def main(app):
    '''Initialize, configure and run server'''
    app = configure_app(app)
    app.run()


if __name__ == '__main__':
    main(app)
