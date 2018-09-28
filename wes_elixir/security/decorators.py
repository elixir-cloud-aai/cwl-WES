from connexion.exceptions import Unauthorized
from connexion import request
from flask import current_app
from functools import wraps
import logging

from jwt import decode

from wes_elixir.config.config_parser import get_conf


# Get logger instance
logger = logging.getLogger(__name__)


def auth_token_optional(fn):

    '''
    If protect is True, the decorator will ensure that the requester has a 
    valid access token before allowing the endpoint to be called.
    '''

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if get_conf(current_app.config, 'security', 'enable_authentication'):
            token = _parse_jwt_from_header(
                header_name=get_conf(current_app.config, 'security', 'jwt', 'header_name'),
                expected_prefix=get_conf(current_app.config, 'security', 'jwt', 'token_prefix'),
            )
            try:
                token_data = decode(
                    jwt=token,
                    key=get_conf(current_app.config, 'security', 'jwt', 'public_key'),
                    algorithms=get_conf(current_app.config, 'security', 'jwt', 'algorithm'),
                    verify=True,
                )
                return fn(token_data=token_data, *args, **kwargs)
            except Exception as e:
                logger.warning("Authentication token could not be decoded. Original error message: {type}: {msg}".format(
                    type=type(e).__name__,
                    msg=e,
                ))
                raise Unauthorized
        else:
            return fn(*args, **kwargs)
    return wrapper


def _parse_jwt_from_header(header_name='Authorization', expected_prefix='Bearer'):
    # TODO: Add custom errors

    '''Parse authentication token from HTTP header'''
    
    # Ensure that authorization header is present
    jwt_header = request.headers.get(header_name, None)
    if not jwt_header:
        logger.warning("No HTTP header with name '{header_name}' found.".format(
            header_name=header_name,
        ))
        raise Unauthorized

    # Ensure that authorization header is formatted correctly
    try:
        (prefix, token) = jwt_header.split()
    except ValueError as e:
        logger.warning("Authentication header is malformed. Original error message: {type}: {msg}".format(
            type=type(e).__name__,
            msg=e,
        ))
        raise Unauthorized
    if prefix != expected_prefix:
        logger.warning("Expected token prefix in authentication header is '{expected_prefix}', but '{prefix}' was found.".format(
            expected_prefix=expected_prefix,
            prefix=prefix,
        ))
        raise Unauthorized

    # Return token
    return token