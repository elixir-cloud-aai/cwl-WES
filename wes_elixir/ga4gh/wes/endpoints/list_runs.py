"""Utility function for GET /runs endpoint."""

import logging

from typing import Dict

from wes_elixir.config.config_parser import get_conf


# Get logger instance
logger = logging.getLogger(__name__)


# Utility function for endpoint GET /runs
def list_runs(
    config: Dict,
    *args,
    **kwargs
) -> Dict:
    """Lists IDs and status for all workflow runs."""
    collection_runs = get_conf(config, 'database', 'collections', 'runs')

    # TODO: stable ordering (newest last?)
    # TODO: implement next page token

    # Fall back to default page size if not provided by user
    # TODO: uncomment when implementing pagination
    # if 'page_size' in kwargs:
    #     page_size = kwargs['page_size']
    # else:
    #     page_size = (
    #         cnx_app.app.config
    #         ['api']
    #         ['endpoint_params']
    #         ['default_page_size']
    # )

    # Query database for workflow runs
    if 'user_id' in kwargs:
        filter_dict = {'user_id': kwargs['user_id']}
    else:
        filter_dict = {}
    cursor = collection_runs.find(
        filter=filter_dict,
        projection={
            'run_id': True,
            'state': True,
            '_id': False,
        }
    )

    runs_list = list()
    for record in cursor:
        runs_list.append(record)

    response = {
        'next_page_token': 'token',
        'runs': runs_list
    }
    return response
