from functools import wraps
from itertools import chain
import logging
import os

import yaml

from addict import Dict


# Get logger instance
logger = logging.getLogger(__name__)


class YAMLConfigParser(Dict):

    '''
    Config parser for YAML files. Allows sequential updating of configs via file paths and
    environment variables. Makes use of the `addict` package for updating config dictionaries.
    '''

    #def __init__(self, config=None):
    #    self.config = Dict(config)


    def update_from_yaml(
        self,
        config_paths=[],
        config_vars=[],
    ):

        '''
        Update config dictionary from file paths or environment variables pointing to one or more
        YAML files. Multiple file paths and environment variables are accepted. Moreover, a given
        environment variable may point to several files, with paths separated by colons. All
        available file paths/pointers are used to update the dictionary in a sequential order, with
        nested dictionary entries being successively and recursively overridden. In other words: if
        a given nested dictionary key occurs in multiple YAML files, its last value will be
        retained. File paths in the `config_paths` list are used first (lowest precedence), from
        the first to the last item/path, followed by file paths pointed to by the environment
        variables in `config_vars` (hightest precedence), form the first to the last item/variable.
        If a given variable points to multiple file paths, these will be used for updating from
        the first to the last path. 

        :param config_paths: List of YAML file paths
        :param config_vars: List of environment variables, each pointing to one or more YAML files,
                           separated by colons; unset variables are ignored
        '''

        # Get ordered list of file paths
        paths = config_paths + [os.environ.get(var) for var in config_vars]
        paths = list(filter(None, paths))
        paths = [item.split(':') for item in paths]
        paths = list(chain.from_iterable(paths))
        logger.warning("PATHS: {}".format(paths))

        # Iterate over file paths
        for path in paths:

            # Otherwise, get config from file path
            try:
                self.__update_from_path(path)

            except (FileNotFoundError, PermissionError):
                raise

        # Return paths that were used to update the dictionary
        return ':'.join(paths)
    

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
            logger.exception("Config file corrupt. Execution aborted. Original error message: {type}: {msg}".format(
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