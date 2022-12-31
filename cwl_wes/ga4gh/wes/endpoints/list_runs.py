"""Utility function for GET /runs endpoint."""
import logging
from typing import Dict

from bson.objectid import ObjectId
from pymongo.collection import Collection
from flask import Config


# Get logger instance
logger = logging.getLogger(__name__)


# Utility function for endpoint GET /runs
def list_runs(
    config: Config,
    *args,
    **kwargs
) -> Dict:
    """Lists IDs and status for all workflow runs."""
    collection_runs: Collection = config.foca.db.dbs['cwl-wes-db'].collections['runs'].client

    # Fall back to default page size if not provided by user
    if 'page_size' in kwargs:
        page_size = kwargs['page_size']
    else:
        page_size = config.foca.custom.controller.default_page_size

    # Extract/set page token
    if 'page_token' in kwargs:
        page_token = kwargs['page_token']
    else:
        page_token = ''

    # Initialize filter dictionary
    filter_dict = {}

    # Add filter for user-owned runs if user ID is available
    if 'user_id' in kwargs:
        filter_dict['user_id'] = kwargs['user_id']
    
    # Add pagination filter based on last object ID
    if page_token != '':
        filter_dict['_id'] = {'$lt': ObjectId(page_token)}

    # Query database for workflow runs
    cursor = collection_runs.find(
        filter=filter_dict,
        projection={
            'run_id': True,
            'api.state': True,
        }
    # Sort results by descending object ID (+/- newest to oldest)
    ).sort(
        '_id', -1
    # Implement page size limit
    ).limit(
        page_size
    )

    # Convert cursor to list
    runs_list = list(cursor)

    # Get next page token from ID of last run in cursor
    if runs_list:
        next_page_token = str(runs_list[-1]['_id'])
    else:
        next_page_token = ''

    # Reshape list of runs
    for run in runs_list:
        del run['_id']
        run['state'] = run['api']['state']
        del run['api']

    # Build and return response
    return {
        'next_page_token': next_page_token,
        'runs': runs_list
    }
