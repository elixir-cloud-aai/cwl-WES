"""Controller for the `/service-info route."""

import logging
from typing import Dict

from bson.objectid import ObjectId
from flask import current_app
from pymongo.collection import Collection

from cwl_wes.exceptions import (
    NotFound,
)
from cwl_wes.ga4gh.wes.states import States

logger = logging.getLogger(__name__)


class ServiceInfo:
    """Class for WES API service info server-side controller methods.

    Creates service info upon first request, if it does not exist.

    Attributes:
        db_collections: FOCA MongoDB collections.
        db_client: Database collection storing service info objects.
        object_id: Database identifier for service info.
    """

    def __init__(self) -> None:
        """Construct class instance."""
        self.db_collections = current_app.config.foca.db.dbs[
            "cwl-wes-db"
        ].collections
        self.db_client: Collection = self.db_collections["service_info"].client
        self.object_id: str = "000000000000000000000000"

    def get_service_info(self, get_counts: bool = True) -> Dict:
        """Get latest service info from database.

        Args:
            get_counts: Whether system state counts should be returned.

        Returns:
            Latest service info details.

        Raises:
            NotFound: Service info was not found.
        """
        service_info = self.db_client.find_one(
            {"_id": ObjectId(self.object_id)},
            {"_id": False},
        )
        if service_info is None:
            raise NotFound
        if get_counts:
            service_info["system_state_counts"] = self._get_state_counts()
        return service_info

    def set_service_info(self, data: Dict) -> None:
        """Create or update service info.

        Arguments:
            data: Dictionary of service info values. Cf.
        """
        self.db_client.replace_one(
            filter={"_id": ObjectId(self.object_id)},
            replacement=data,
            upsert=True,
        )
        logger.info(f"Service info set: {data}")

    def init_service_info_from_config(self) -> None:
        """Initialize service info from config.

        Set service info only if it does not yet exist.
        """
        service_info_conf = current_app.config.foca.custom.service_info.dict()
        try:
            service_info_db = self.get_service_info(get_counts=False)
        except NotFound:
            logger.info("Initializing service info.")
            self.set_service_info(data=service_info_conf)
            return
        if service_info_db != service_info_conf:
            logger.info(
                "Service info configuration changed. Updating service info."
            )
            self.set_service_info(data=service_info_conf)
            return
        logger.debug("Service info already initialized and up to date.")

    def _get_state_counts(self) -> Dict[str, int]:
        """Get current system state counts."""
        current_counts = {state: 0 for state in States.ALL}
        db_client_runs: Collection = self.db_collections["runs"].client
        cursor = db_client_runs.find(
            filter={},
            projection={
                "run_log.state": True,
                "_id": False,
            },
        )
        for record in cursor:
            current_counts[record["run_log"]["state"]] += 1
        return current_counts
