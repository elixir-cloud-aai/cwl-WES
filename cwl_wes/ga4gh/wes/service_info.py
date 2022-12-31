"""Controllers for the `/service-info route."""

import logging
from typing import Dict

from bson.objectid import ObjectId
from foca.models.config import Config
from flask import current_app
from pymongo.collection import Collection

from cwl_wes.exceptions import (
    NotFound,
)
from cwl_wes.ga4gh.wes.states import States

logger = logging.getLogger(__name__)


class ServiceInfo:
    def __init__(self) -> None:
        """Class for WES API service info server-side controller methods.

        Creates service info upon first request, if it does not exist.

        Attributes:
            config: App configuration.
            foca_config: FOCA configuration.
            db_client_service_info: Database collection storing service info
                objects.
            db_client_runs: Database collection storing workflow run objects.
            object_id: Database identifier for service info.
        """
        self.config: Dict = current_app.config
        self.foca_config: Config = self.config.foca
        self.db_client_service_info: Collection = (
            self.foca_config.db.dbs["cwl-wes-db"]
            .collections["service_info"]
            .client
        )
        self.db_client_runs: Collection = (
            self.foca_config.db.dbs["cwl-wes-db"].collections["runs"].client
        )
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
        service_info = self.db_client_service_info.find_one(
            {"_id": ObjectId(self.object_id)},
            {"_id": False},
        )
        if service_info is None:
            raise NotFound
        if get_counts:
            service_info["system_state_counts"] = self._get_state_counts()
        return service_info

    def set_service_info(
        self,
        data: Dict,
    ) -> None:
        """Create or update service info.

        Arguments:
            data: Dictionary of service info values. Cf.
        """
        self.db_client_service_info.replace_one(
            filter={"_id": ObjectId(self.object_id)},
            replacement=data,
            upsert=True,
        )
        logger.info("Service info set.")

    def _get_state_counts(self) -> Dict[str, int]:
        """Gets current system state counts."""
        current_counts = {state: 0 for state in States.ALL}
        cursor = self.db_client_runs.find(
            filter={},
            projection={
                "run_log.state": True,
                "_id": False,
            },
        )
        for record in cursor:
            current_counts[record["run_log"]["state"]] += 1
        return current_counts
