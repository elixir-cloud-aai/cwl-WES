"""Functions that translate DRS URIs into access URLs."""

from fileinput import FileInput
from functools import partial
import logging
import os
import re
from requests.exceptions import ConnectionError
import sys
from typing import Iterator, List, Match, Optional

from drs_cli.client import DRSClient
from drs_cli.errors import InvalidResponseError, InvalidURI
from drs_cli.models import Error
from werkzeug.exceptions import (
    BadRequest,
    InternalServerError,
)


# Get logger instance
logger = logging.getLogger(__name__)


def translate_drs_uris(
    path: str,
    file_types: List[str],
    supported_access_methods: List[str],
    port: Optional[int] = None,
    base_path: Optional[str] = None,
    use_http: bool = False,
) -> None:
    """Replace hostname-based DRS URIs with access links either in a file or,
    recursively, in all files of a directory.

    For hostname-based DRS URIs, cf.
    https://ga4gh.github.io/data-repository-service-schemas/preview/develop/docs/#_hostname_based_drs_uris

    Arguments:
        path: File or directory containing files.
        file_types: Extensions of files to scan.
        supported_access_methods: List of access methods/file transfer
            protocols supported by this service, provided in the order of
            preference.
        port: Port to use when resolving DRS URIs; set to `None` to use default
            port required by the DRS documentation.
        base_path: Base path to use when resolving DRS URIs; set to `None` to
            use default base path as per the DRS specification.
        use_http: When resolving DRS URIs, use the `http` URL schema instead of
            the default `https` required by the DRS
            documentation/specification.
    """
    # define regex for identifying DRS URIs
    _RE_DOMAIN_PART = r"[a-z0-9]([a-z0-9-]{1,61}[a-z0-9]?)?"
    _RE_DOMAIN = rf"({_RE_DOMAIN_PART}\.)+{_RE_DOMAIN_PART}\.?"
    _RE_OBJECT_ID = rf"(?P<drs_uri>drs:\/\/{_RE_DOMAIN}\/\S+)"

    # get absolute paths of file or directory (including subdirectories)
    logger.debug(f"Collecting file(s) for provided path '{path}'...")
    files = (
        abs_paths(
            dir=path,
            file_ext=file_types,
        )
        if os.path.isdir(path)
        else [path]
    )

    # replace any DRS URIs in any file in place
    for _file in files:
        logger.debug(f"Scanning file '{_file}' for DRS URIs...")
        with FileInput(_file, inplace=True) as _f:
            for line in _f:
                sys.stdout.write(
                    re.sub(
                        pattern=_RE_OBJECT_ID,
                        repl=partial(
                            get_replacement_string,
                            ref="drs_uri",
                            supported_access_methods=supported_access_methods,
                            port=port,
                            base_path=base_path,
                            use_http=use_http,
                        ),
                        string=line,
                    ),
                )


def abs_paths(
    dir: str,
    file_ext: List[str],
) -> Iterator[str]:
    """Yields absolute paths of files with the indicated file extensions in
    specified directory and subdirectories.

    Arguments:
        dir: Directory to search files in.
        file_ext: List of file extensions for files to return.

    Returns:
        Generator yielding absolute file paths.
    """
    for dirpath, _, files in os.walk(dir):
        for _file in files:
            if _file.endswith(tuple(file_ext)):
                yield os.path.abspath(os.path.join(dirpath, _file))


def get_replacement_string(
    match: Match,
    ref: str,
    supported_access_methods: List[str],
    port: Optional[int] = None,
    base_path: Optional[str] = None,
    use_http: bool = False,
) -> str:
    """Helper function to get string replacement string.

    Args:
        match: Match object from `re.sub()` call
        ref: Named reference to match of interest.
        supported_access_methods: List of access methods/file transfer
            protocols supported by this service, provided in the order of
            preference.
        port: Port to use when resolving DRS URIs; set to `None` to use default
            port required by the DRS documentation.
        base_path: Base path to use when resolving DRS URIs; set to `None` to
            use default base path as per the DRS specification.
        use_http: When resolving DRS URIs, use the `http` URL schema instead of
            the default `https` required by the DRS
            documentation/specification.

    Returns:
        String replacement string
    """
    return get_access_url_from_drs(
        drs_uri=match.group(ref),
        supported_access_methods=supported_access_methods,
        port=port,
        base_path=base_path,
        use_http=use_http,
    )


def get_access_url_from_drs(
    drs_uri: str,
    supported_access_methods: List[str],
    port: Optional[int] = None,
    base_path: Optional[str] = None,
    use_http: bool = False,
) -> str:
    """
    Arguments:
        drs_uri: A DRS URI pointing to a DRS object.
        supported_access_methods: List of access methods/file transfer
            protocols supported by this service, provided in the order of
            preference.
        port: Port to use when resolving DRS URIs; set to `None` to use default
            port required by the DRS documentation.
        base_path: Base path to use when resolving DRS URIs; set to `None` to
            use default base path as per the DRS specification.
        use_http: When resolving DRS URIs, use the `http` URL schema instead of
            the default `https` required by the DRS
            documentation/specification.

    Returns:
        Access URL for DRS object.

    Raises:
        BadRequest: either `drs_uri` is invalid, a DRS object could not be
            found or a supported access method could not be found for the
            DRS object.
        InternalServerError: either no connection could be made to the DRS
            or the DRS request or response is invalid.
    """
    # instantiate DRS client instance
    try:
        client = DRSClient(
            uri=drs_uri,
            port=port,
            base_path=base_path,
            use_http=use_http,
        )
    except InvalidURI:
        logger.error(f"The provided DRS URI '{drs_uri}' is invalid.")
        raise BadRequest

    # get DRS object
    try:
        object = client.get_object(object_id=drs_uri)
    except (ConnectionError, InvalidResponseError):
        logger.error(f"Could not connect to DRS host for DRS URI '{drs_uri}'.")
        raise InternalServerError
    if isinstance(object, Error):
        if object.status_code == 404:
            logger.error(f"Could not access DRS host for DRS URI '{drs_uri}'.")
            raise BadRequest
        # TODO: handle 401 & 403
        else:
            logger.error(f"DRS returned error: {object}'.")
            raise InternalServerError

    # get access methods and access method types/protocols
    available_methods = object.access_methods
    available_types = [m.type.value for m in available_methods]

    # iterate through supported methods by order of preference
    # TODO: add support for access URL headers
    for supported_method in supported_access_methods:
        try:
            access_url = str(
                available_methods[
                    available_types.index(supported_method)
                ].access_url.url
            )
            logger.info(
                f"Resolved DRS URI '{drs_uri}' to access link '{access_url}'."
            )
            return access_url
        except ValueError:
            continue

    # no method was found
    logger.error(
        f"Could not find a supported access URL for DRS URI '{drs_uri}'."
    )
    raise BadRequest
