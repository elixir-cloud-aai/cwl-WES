from functools import wraps
import logging
import os
import yaml


# Get logger instance
logger = logging.getLogger(__name__)


class YAMLConfigParser(dict):

    '''TODO'''

    def update_from_file_or_env(
        self,
        config_var=None,
        config_path=None
    ):

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


def get_conf_type(
    config,
    *args,
    types=False,
    invert_types=False,
    touchy=True
):

    '''
    Extract the value corresponding to a chain of keys from a nested dictionary.

    :param config: Dictionary containing config values
    :param *args: Keys of nested dictionary, from outer to innermost
    :param types: Tuple of allowed types for return values; no check, if False is If True, a ValueError is raised if the return value is a dictionary
    :param invert_types: Types specified in parameter 'types' are *forbidden*; only relevant if 'types' is not False
    :param touchy: If True, exceptions will raise SystemExit(1); otherwise exceptions are re-raised
    '''

    keys = list(args)

    try:

        val = config[keys.pop(0)]

        while keys:
            val = val[keys.pop(0)]
    
        if types:
            if not invert_types:
                if not isinstance(val, types):
                    raise ValueError("Value '{val}' expected to be of {types}, but is of {type}.".format(
                        val=val,
                        types=types,
                        type=type(val),
                    ))
            else:
                if isinstance(val, types):
                    raise ValueError("Type ({type}) of value '{val}' is not allowed.".format(
                        type=type(val),
                        val=val,
                    ))

    except (AttributeError, KeyError, TypeError, ValueError) as e:

        if touchy:
            logger.critical("Config file corrupt. Execution aborted. Original error message: {type}: {msg}".format(
                type=type(e).__name__,
                msg=e,
            ))
            raise SystemExit(1)
        
        else: raise

    else: return(val)


def get_conf(
    config,
    *args,
    touchy=True
):

    '''
    Shortcut for get_conf_type(config, *args, types=(dict, list), invert_types=True); extracts only 'leafs' of nested dictionary.

    :param config: Dictionary containing config values
    :param *args: Keys of nested dictionary, from outer to innermost
    :param touchy: If True, exceptions will raise SystemExit(1); otherwise exceptions are re-raised
    '''
    
    return get_conf_type(
        config,
        *args,
        types=(dict, list),
        invert_types=True,
        touchy=touchy
    )