from datetime import datetime, timezone
from services.db import PyMongoUtils


class ServiceInfo:

    def __init__(self, collection, config, version):
        '''Instantiate ServiceInfo object'''

        # Set collection
        self.collection = collection

        # Set service info
        self.service_info = config

        # Add version
        self.service_info['tags']['version'] = version

        # Initialize service info object id
        self.latest_object_id = PyMongoUtils.find_id_latest(self.collection)

        # Initialize complete service info object
        self.service_info_complete = None

        # Initialize system state counts
        self.init_system_state_counts()

        # Set service info
        self.set_service_info()


    def set_service_info(self):
        '''Set service info'''

        # Write service info to database if unset or differs from last version
        if not self.service_info == PyMongoUtils.find_one_latest(self.collection):
            self.latest_object_id = self.collection.insert(self.service_info)


    def get_service_info(self):
        '''Returns readily formatted service info or None'''

        # Query database for latest service info entry
        self.service_info_complete = PyMongoUtils.find_one_by_id(self.collection, self.latest_object_id)

        # If service entry object was not found...
        if self.service_info_complete is None:

            # Set service info again
            self.set_service_info()

            # Query database for latest service info entry
            self.service_info_complete = PyMongoUtils.find_one_by_id(self.collection, self.latest_object_id)

        # Else...
        else:

            # Add current system state counts
            self.service_info_complete['system_state_counts'] = self.get_system_state_counts()

            # Add timestamps
            self.service_info_complete['tags']['timestamp_last_service_info_update'] = self.latest_object_id.generation_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
            self.service_info_complete['tags']['timestamp_current'] = datetime.now().isoformat()

        # Return service info
        return self.service_info_complete


    def init_system_state_counts(self):
        '''Initialize system state counts'''

        # Set all state counts to zero
        # TODO: Get states programmatically
        self.system_state_counts = {
            "UNKNOWN": 0,
            "QUEUED": 0,
            "INITIALIZING": 0,
            "RUNNING": 0,
            "PAUSED": 0,
            "COMPLETE": 0,
            "EXECUTOR_ERROR": 0,
            "SYSTEM_ERROR": 0,
            "CANCELED": 0
        }


    def get_system_state_counts(self):
        '''Get current system state counts'''
        # TODO: Get numbers from database

        # Return counts
        return(self.system_state_counts)
