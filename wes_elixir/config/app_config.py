import logging
import os
import sys

from wes_elixir.config.config_parser import YAMLConfigParser


# Get logger instance
logger = logging.getLogger(__name__)


def parse_app_config(
    config_var=None,
    default_path=os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app_config.yaml')),
):

    '''Parse configuration file and add to connexion app'''

    # Create parser instance
    config = YAMLConfigParser()

    # Parse config
    try:
        path = config.update_from_file_or_env(config_var=config_var, config_path=default_path)

    # Abort if no config file was found/accessible 
    except (FileNotFoundError, PermissionError):
        logger.critical("No config file found. A config file needs to be available at '{default_path}'. Alternatively, point the environment variable '{config_var}' to its location. Execution aborted.".format(
                default_path=default_path,
                config_var=config_var,
        ))
        raise SystemExit(1)

    # Log info 
    else:
        logger.info("App config file loaded from '{path}'.".format(path=path))
    
    # Return config
    return config