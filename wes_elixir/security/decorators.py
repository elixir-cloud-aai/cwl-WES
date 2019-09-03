"""Decorator and utility functions for protecting access to endpoints."""

from connexion.exceptions import Unauthorized
from connexion import request
from flask import current_app
from functools import wraps
import logging
from typing import (Callable, Iterable, Mapping)

from jwt import (decode, get_unverified_header, algorithms)
import requests
import json

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

            # Decode the token (without verification)
            try:
                token_data = decode_token(
                    token=token,
                    to_verify=False,
                    algorithms=get_conf(
                        current_app.config,
                        'security',
                        'jwt',
                        'algorithm'
                    ),
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

            # infer the header data from the token
            try:
                token_header_data = get_unverified_header(token)
            except Exception as e:
                logger.error(
                    (
                        'Authentication token without header. Original '
                        'error message: {type}: {msg}'
                    ).format(
                        type=type(e).__name__,
                        msg=e,
                    )
                )
                raise Unauthorized

            # validation steps
            identity_claim = get_conf(
                current_app.config,
                'security',
                'jwt',
                'identity_claim'
            )
            issuer_claim = "iss"

            # only accept the token if it contains the issuer claim ("iss")
            validate_claims(
                token_data=token_data,
                required_claims=[issuer_claim, identity_claim],
            )
            # store the OIDC provider (aka issuer) base-url
            iss_base_url = token_data['iss']

            # authenticate the token through successful access to the
            # userinfo endpoint
            try:
                _auth_through_uinfo_endpt(
                base_url = iss_base_url,
                token=token,
                ok_status_code = 200
                )
            except Exception as e:
                logger.error(
                    (
                        'Initial token authentication failed. Original '
                        'error message: {type}: {msg}'
                    ).format(
                        type=type(e).__name__,
                        msg=e,
                    )
                )
                # try authentication through public key
                # TODO: check if logger.error can be used
                #       for status messages, too
                # TODO: check if the ok status should be in the config
                public_key = infer_public_key(
                    token_data=token_data,
                    header_data=token_header_data,
                    base_url=iss_base_url,
                    ok_status=200
                )
                # TODO: decode_token should be run
                #       within a try except block (see commented block below).
                #       Is it possible to do this here since we are
                #       already within an except block?
                try:
                    decode_token(
                        token=token,
                        to_verify=True,
                        key=public_key,
                        algorithms=get_conf(
                            'security',
                            'jwt',
                            'algorithm'
                        )
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

            # # Decode token
            # try:
            #     token_data = decode_token(
            #         token=token,
            #         to_verify=True,
            #         key=get_conf(
            #             current_app.config,
            #             'security',
            #             'jwt',
            #             'public_key'
            #         ),
            #         algorithms=get_conf(
            #             current_app.config,
            #             'security',
            #             'jwt',
            #             'algorithm'
            #         )
            #     )
            # except Exception as e:
            #     logger.error(
            #         (
            #             'Authentication token could not be decoded. Original '
            #             'error message: {type}: {msg}'
            #         ).format(
            #             type=type(e).__name__,
            #             msg=e,
            #         )
            #     )
            #     raise Unauthorized

            # # Validate claims
            # identity_claim = get_conf(
            #     current_app.config,
            #     'security',
            #     'jwt',
            #     'identity_claim'
            # )
            # validate_claims(
            #     token_data=token_data,
            #     required_claims=[identity_claim],
            # )

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

def decode_token(
    # TODO: specify the type for key which can be
    #       an instance of cryptography.hazmat.backends.openssl.rsa._RSAPublicKey
    token: str,
    key = None,
    algorithms: Iterable[str] = [],
    to_verify: bool = True
) -> str:
    """Decode an ID token (and optionally verify it with a public key)"""
    if to_verify:
        return (decode(jwt=token,
                    key=key,
                    algorithms=algorithms,
                    verify=True
        ))
    else:
        return (decode(jwt=token,
                    key=key,
                    algorithms=algorithms,
                    verify=True
        ))

# TODO: specify return type
def infer_public_key(
    token: str = '',
    base_url: str = '',
    token_data: Mapping = {},
    header_data: Mapping = {},
    ok_status: int = 200
):
    """Infer the corresponding public key from the
    issuer based on the ID token
    """

    # only accept the token if its header contains the kid property
    validate_claims(
        token_data = header_data,
        required_claims=['kid']
    )
    # store the key id
    token_kid = header_data['kid']

    # try to obtain a public key based on the avaiblable token
    # default: use a hard-coded public key
    default_public_key = get_conf(
        current_app.config,
        'security',
        'jwt',
        'public_key'
    )
    try:
        issuer_public_keys = get_issuer_public_keys(
            base_url = base_url,
            ok_status = ok_status
        )
    except Exception as e:
        logger.error(
            (
                'Fall back to default public key. Original '
                        'error message: {type}: {msg}'
                    ).format(
                        type=type(e).__name__,
                        msg=e,
                    )
            )
        return default_public_key

    if not token_kid in issuer_public_keys:
        logger.error(
            (
                "token key id not found in issuer public keys."
                "Use default public key instead"
            )
        )
        return default_public_key

    return issuer_public_keys[token_kid]
    
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
            logger.error("Required claim '{claim}' not found in given token data.".format(
                claim=claim,
            ))
            raise Unauthorized

def get_entry_from_discovery_doc(
        base_url: str = '',
        ok_status_code: int = 200,
        entry: str = ''
    ) -> str:
    """query the issuer discovery document to retrieve the value
    for a specified field
    """
    base_url_no_end_slash = base_url.rstrip("/")
    discovery_doc_url = ("%s./well-known/openid-configuration"
        % base_url_no_end_slash)

    discovery_doc_response = requests.get(discovery_doc_url)

    _validate_response(
        discovery_doc_response,
        ok_status_code = ok_status_code
    )
    discovery_doc_json = discovery_doc_response.json()

    if entry not in discovery_doc_json:
        logger.error("Required entry '{entry}' not found in discovery document.".format(
            entry=entry,
        ))
        raise Exception
    return discovery_doc_json[entry]

def _auth_through_uinfo_endpt(
    base_url: str = "",
    token: str = "",
    ok_status_code: int = 200
):
    """Test, whether the ID token allows to access
    the userinfo endpoint
    """
    uinfo_endpt_url = get_entry_from_discovery_doc(
        base_url = base_url,
        entry = "userinfo_endpoint",
        ok_status_code = ok_status_code
    )
    uinfo_endpt_request_header = {
        'Authorization': 'Bearer %s' % token
    }
    uinfo_endpt_response = requests.get(
        uinfo_endpt_url,
        headers=uinfo_endpt_request_header
    )
    _validate_response(uinfo_endpt_response, ok_status_code = 200)

def get_issuer_public_keys(
    base_url: str='',
    ok_status: int=200
) -> Mapping:
    """Infer the list of public keys listed by the issuer of
    the ID token
    """
    # get the jwks_uri from the discovery document
    jwks_uri = get_entry_from_discovery_doc(
        base_url = base_url,
        entry = "jwks_uri",
        ok_status_code = ok_status
    )

    jwks_response = requests.get(jwks_uri)
    try:
        _validate_response(jwks_response, ok_status_code = ok_status)
    except Exception as e:
        logger.error(
            (
                'No valid response obtained from the jwks_uri. Original'
                'error message: {type}: {msg}'
            ).format(
                type=type(e).__name__,
                msg=e
            )
        )
        raise
    jwks_response_json = jwks_response.json()

    # iterate over all key ids and store their corresponding public keys
    iss_public_keys = {}
    for jwk in jwks_response_json['keys']:
        kid = jwk['kid']
        iss_public_keys[kid] = algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

    if len(iss_public_keys) == 0:
        raise Exception
    
    return iss_public_keys

# TODO: specify the input type for response (requests.response object)
def _validate_response(
    response,
    ok_status_code: int = 200
):
    """ Ensures response is valid.
    Parameters
    ----------
    response: requests.response
        A requests.response object
    Raises
    ------
    ValueError
        If an invalid return status is obtained
    """
    ###
    # TODO: implement meaningful error and error message
    ###
    if response.status_code != ok_status_code:
        raise ValueError()

