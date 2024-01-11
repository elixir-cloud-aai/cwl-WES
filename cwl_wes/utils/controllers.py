"""Controller utilities."""

import logging
from typing import Dict, Optional

from connexion.exceptions import Forbidden
from flask import Config
from pymongo.collection import Collection

from cwl_wes.exceptions import WorkflowNotFound

logger = logging.getLogger(__name__)


def get_document_if_allowed(
    config: Config,
    run_id: str,
    projection: Dict,
    user_id: Optional[str],
) -> Dict:
    """Get document from database, if allowed.

    Args:
        config: Flask configuration object.
        run_id: Workflow run ID.
        projection: Projection for database query.
        user_id: User ID.

    Raises:
        WorkflowNotFound: If workflow run is not found.
        Forbidden: If user is not allowed to access workflow run.

    Returns:
        Document from database.
    """
    collection_runs: Collection = (
        config.foca.db.dbs["cwl-wes-db"].collections["runs"].client
    )
    document = collection_runs.find_one(
        filter={"run_id": run_id},
        projection=projection,
    )

    if document is None:
        raise WorkflowNotFound

    if document["user_id"] != user_id:
        raise Forbidden

    return document
