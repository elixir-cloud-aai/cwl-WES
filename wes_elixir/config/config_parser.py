from functools import wraps
import logging
import os
import yaml


# Get logger instance
logger = logging.getLogger(__name__)


class YAMLConfigParser(dict):

    '''TODO'''

    def update_from_file_or_env(self, config_var=None, config_path=None):

        '''
        Update dict from a YAML file path or environment variable pointing to a YAML file.
        If both an environment variable and a file path are specified, the variable takes
        precendence, and the file path is used as a fallback.

        :param config_var: Environment variable pointing to YAML file
        :param config_path: YAML file path
        '''

        # If defined, get config from environment variable
        try:
            self.__update_from_path(os.environ[config_var])
            return os.environ[config_var]

        except KeyError:
            pass

        except FileNotFoundError:
            logger.warning("Environment variable '{config_var}' set but no file found at '{path}'.\n\tFalling back to default path '{default_path}'.".format(
                config_var=config_var,
                path=os.getenv(config_var),
                default_path=config_path,
            ))

        except PermissionError:
            logger.warning("Environment variable '{config_var}' set but file '{path}' is not readable.\n\tFalling back to default path '{default_path}'.".format(
                config_var=config_var,
                path=os.getenv(config_var),
                default_path=config_path,
            ))

        # Otherwise, get config from file path
        try:
            self.__update_from_path(config_path)
            return config_path

        except (FileNotFoundError, PermissionError):
            raise


    def __update_from_path(self, path):
        with open(path) as f:
            self.update(yaml.safe_load(f))


def get_conf(
    config,
    *args,
    leafs_only=True,
    touchy=True
):

    '''
    Extract the value corresponding to a chain of keys from a nested dictionary.

    :param config: Dictionary containing config values
    :param leafs_only: If True, a ValueError is raised if the return value is a dictionary
    :param touchy: If True, exceptions will raise SystemExit(1); otherwise exceptions are re-raised
    '''

    keys = list(args)

    try:

        val = config[keys.pop(0)]

        while keys:
            val = val[keys.pop(0)]
    
        if leafs_only and isinstance(val, dict):
            raise ValueError("Value '{val}' expected to be leaf, but is a dict.".format(val=val))

    except (AttributeError, KeyError, TypeError, ValueError) as e:

        if touchy:
            logger.critical("Config file corrupt. Execution aborted. Original error message: {type}: {msg}".format(type=type(e).__name__, msg=e))
            raise SystemExit(1)
        
        else: raise

    else: return(val)