import configloader
import flask_cors
import flask_pymongo
import os
import string
import sys
from connexion import App
from connexion.exceptions import ExtraParameterProblem, Forbidden, Unauthorized
from ga4gh.utils.runs import Runs
from ga4gh.utils.service_info import ServiceInfo
from services.error_handling import error_handlers as eh
from services.error_handling.custom_errors import BadRequest, InternalServerError, WorkflowNotFound


# Global app parameters
version = "0.2.0"


# Parse config file
config = configloader.ConfigLoader()
if 'WES_CONFIG' not in os.environ:
    sys.exit("Environment variable 'WES_CONFIG' not set.\nExecution aborted.")
if not os.path.isfile(os.environ['WES_CONFIG']):
    sys.exit("No config file found at location specified in 'WES_CONFIG': {}.\nExecution aborted.".format(os.environ['WES_CONFIG']))
config.update_from_yaml_env('WES_CONFIG')


# Add debug config
if config['server']['debug']:
    if 'WES_CONFIG_DEBUG' not in os.environ:
        sys.exit("Environment variable 'WES_CONFIG_DEBUG' not set.\nExecution aborted.")
    if not os.path.isfile(os.environ['WES_CONFIG_DEBUG']):
        sys.exit("No config file found at location specified in 'WES_CONFIG_DEBUG': {}.\nExecution aborted.".format(os.environ['WES_CONFIG_DEBUG']))
    config.update_from_yaml_env('WES_CONFIG_DEBUG')


# Initialize app
try:
    app = App(
        __name__,
        specification_dir=config['openapi']['path'],
        swagger_ui=True,
        swagger_json=True,
    )
except KeyError:
    sys.exit("Config file corrupt. Execution aborted.")


# Add error handlers
app.add_error_handler(ExtraParameterProblem, eh.handle_bad_request)
app.add_error_handler(BadRequest, eh.handle_bad_request)
app.add_error_handler(Unauthorized, eh.handle_unauthorized)
app.add_error_handler(Forbidden, eh.handle_forbidden)
app.add_error_handler(WorkflowNotFound, eh.handle_workflow_not_found)
app.add_error_handler(InternalServerError, eh.handle_internal_server_error)
# Workaround for adding a custom handler for `connexion.problem` responses
# Responses from request and paramater validators are not raised and cannot be intercepted by `add_error_handler`
# See here: https://github.com/zalando/connexion/issues/138
@app.app.after_request
def rewrite_bad_request(response):
    if response.status_code == 400 and response.data.decode('utf-8').find('"title":') != None:
        response = eh.handle_bad_request(400)
    return response


# Initialize database
try:
    mongo = flask_pymongo.PyMongo(app.app, uri="mongodb://{host}:{port}/{name}".format(
        host=config['database']['host'],
        port=config['database']['port'],
        name=config['database']['name']
    ))
    db = mongo.db[config['database']['name']]
except KeyError:
    sys.exit("Config file corrupt. Execution aborted.")


# Add database collections
db_service_info = mongo.db['service-info']
db_runs = mongo.db['runs']
db_runs.create_index([('run_id', flask_pymongo.ASCENDING)], unique=True)


# Instantiate service info object
service_info = ServiceInfo(
    collection=db_service_info,
    runs=db_runs,
    config=config['service_info'],
    version=version
)


# Instantiate runs object
if config['server']['debug']:
    runs = Runs(
        collection=db_runs,
        index='run_id',
        run_id_length=config['database']['run_id']['length'],
        run_id_charset=eval(config['database']['run_id']['charset']),
        default_page_size=config['api_endpoints']['default_page_size'],
        url=config['tes']['url'],
        debug=config['server']['debug'],
        dummy_request=config['debug_params']['dummy_runs']['request'],
        limit=config['debug_params']['dummy_runs']['limit']
    )
else:
    runs = Runs(
        collection=db_runs,
        index='run_id',
        run_id_length=config['database']['run_id']['length'],
        run_id_charset=eval(config['database']['run_id']['charset']),
        default_page_size=config['api_endpoints']['default_page_size'],
        url=config['tes']['url'],
        debug=config['server']['debug']
    )


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
    flask_cors.CORS(app)

    return(app)


def add_openapi(app):
    '''Add OpenAPI specification to connexion app instance'''
    try:
        app.add_api(
            config['openapi']['yaml_specs'],
            base_path="/ga4gh/wes/v1",
            strict_validation=True,
            validate_responses=True,
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
