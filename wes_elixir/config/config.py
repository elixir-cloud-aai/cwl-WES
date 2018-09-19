import os
import sys

from configloader import ConfigLoader


def config_connexion_app(cnx_app):
    '''Parse configuration file and add to connexion app'''

    # Parse config file
    config = ConfigLoader()

    # Exit if `WES_CONFIG` environment variable is not defined
    if 'WES_CONFIG' not in os.environ:
        sys.exit("Environment variable 'WES_CONFIG' not set.\nExecution aborted.")

    # Exit if config file was not found
    if not os.path.isfile(os.environ['WES_CONFIG']):
        sys.exit("No config file found at location specified in 'WES_CONFIG': {}.\nExecution aborted.".format(os.environ['WES_CONFIG']))

    # Parse configuration file
    config.update_from_yaml_env('WES_CONFIG')

    # Add config to connexion app
    cnx_app = __add_config_to_app(config, cnx_app)

    # Return connexion app instance
    return cnx_app


def __add_config_to_app(config, cnx_app):
    '''Add configuration to Flask app and replace default connexion and Flask settings'''

    # Add configuration to Flask app config
    cnx_app.app.config.update(config)

    # Replace default connexion app config
    cnx_app.host = config['server']['host']
    cnx_app.port = config['server']['port']
    cnx_app.debug = config['server']['debug']

    # Replace default Flask app config
    cnx_app.app.config['DEBUG'] = config['server']['debug']
    cnx_app.app.config['ENV'] = config['server']['env']
    cnx_app.app.config['TESTING'] = config['server']['testing']

    # Return connexion app instance
    return cnx_app
