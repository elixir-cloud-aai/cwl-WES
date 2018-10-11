import logging
import os
import sys

from wes_elixir.config.config_parser import YAMLConfigParser


# Get logger instance
logger = logging.getLogger(__name__)


def parse_app_config(
    config_var=None,
    default_path=os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app_config.yaml'))
):

    '''Parse configuration file and add to Connexion app'''

    # Create parser instance
    config = YAMLConfigParser()

    # Parse config
    try:
        paths = config.update_from_yaml(
            config_paths=[default_path],
            config_vars=[config_var],
        )

    # Abort if a config file was not found/accessible 
    except (FileNotFoundError, PermissionError) as e:
        logger.exception("Config file not found. Ensure that default config file is available and accessible at '{default_path}'. If '{config_var}' is set, further ensure that the file or files it points are available and accessible. Execution aborted. Original error message: {type}: {msg}".format(
            default_path=default_path,
            config_var=config_var,
            type=type(e).__name__,
            msg=e,
        ))
        raise SystemExit(1)

    # Log info 
    else:
        logger.info("App config loaded from '{paths}'.".format(paths=paths))
    
    # Return config
    return config