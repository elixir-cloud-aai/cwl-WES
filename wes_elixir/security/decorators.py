"""Decorator and utility functions for protecting access to endpoints."""

from connexion.exceptions import Unauthorized
from connexion import request
from flask import current_app
from functools import wraps
import logging
from typing import (Callable, Iterable, Mapping)

from jwt import decode

from wes_elixir.config.config_parser import get_conf


# Get logger instance
logger = logging.getLogger(__name__)


def auth_token_optional(fn: Callable) -> Callable:
    """The decorator protects an endpoint from being called without a valid
    authorization token.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):

        # Check if authentication is enabled
        if get_conf(current_app.config, 'security', 'authorization_required'):

            # Parse token from HTTP header
            token = parse_jwt_from_header(
                header_name=get_conf(
                    current_app.config,
                    'security',
                    'jwt',
                    'header_name'
                ),
                expected_prefix=get_conf(
                    current_app.config,
                    'security',
                    'jwt',
                    'token_prefix'
                ),
            )

            # Decode token
            try:
                token_data = decode(
                    jwt=token,
                    key=get_conf(
                        current_app.config,
                        'security',
                        'jwt',
                        'public_key'
                    ),
                    algorithms=get_conf(
                        current_app.config,
                        'security',
                        'jwt',
                        'algorithm'
                    ),
                    verify=True,
                )
            except Exception as e:
                logger.error(
                    (
                        'Authentication token could not be decoded. Original '
                        'error message: {type}: {msg}'
                    ).format(
                        type=type(e).__name__,
                        msg=e,
                    )
                )
                raise Unauthorized

            # Validate claims
            identity_claim = get_conf(
                current_app.config,
                'security',
                'jwt',
                'identity_claim'
            )
            validate_claims(
                token_data=token_data,
                required_claims=[identity_claim],
            )

            # Extract user ID
            user_id = token_data[identity_claim]

            # Return wrapped function with token data
            return fn(
                token=token,
                token_data=token_data,
                user_id=user_id,
                *args,
                **kwargs
            )

        # Return wrapped function without token data
        else:
            return fn(*args, **kwargs)

    return wrapper


def parse_jwt_from_header(
    header_name: str ='Authorization',
    expected_prefix: str ='Bearer'
) -> Mapping:
    """Parses authorization token from HTTP header."""
    # TODO: Add custom errors
    # Ensure that authorization header is present
    auth_header = request.headers.get(header_name, None)
    if not auth_header:
        logger.error("No HTTP header with name '{header_name}' found.".format(
            header_name=header_name,
        ))
        raise Unauthorized

    # Ensure that authorization header is formatted correctly
    try:
        (prefix, token) = auth_header.split()
    except ValueError as e:
        logger.error(
            (
                'Authentication header is malformed. Original error message: '
                '{type}: {msg}'
            ).format(
                type=type(e).__name__,
                msg=e,
            )
        )
        raise Unauthorized
    if prefix != expected_prefix:
        logger.error(
            (
                'Expected token prefix in authentication header is '
                "'{expected_prefix}', but '{prefix}' was found."
            ).format(
                expected_prefix=expected_prefix,
                prefix=prefix,
            )
        )
        raise Unauthorized

    return token


def validate_claims(
    token_data: Mapping,
    required_claims: Iterable[str] = []
):
    """Validates token claims."""
    # Check for existence of required claims
    for claim in required_claims:
        if claim not in token_data:
            logger.error("Required claim '{claim}' not found in token.".format(
                claim=claim,
            ))
            raise Unauthorized
