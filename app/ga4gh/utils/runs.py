from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from random import choice
from services.db import PyMongoUtils


class Runs:

    def __init__(self, collection, run_id_length, run_id_charset, debug=False, dummy_request=None, limit=None):
        '''Instantiate ServiceInfo object'''

        # Set run mode
        self.debug = debug

        # Set collection
        self.collection = collection

        # Set run id generation parameters
        self.run_id_length = run_id_length
        self.run_id_charset = run_id_charset

        # Initialize service info object id
        self.latest_object_id = PyMongoUtils.find_id_latest(self.collection)

        # DEBUG: Save dummy workflow in database
        if self.debug:
            self.insert_workflow_run(dummy_request, limit=limit)


    def __create_run_id(self):
        '''Create random run id'''
        return ''.join(choice(self.run_id_charset) for _ in range(self.run_id_length))


    def __init_run_document(self, request):
        '''Initialize workflow run document'''

        # Initialize document
        document = dict()

        # Add required keys
        document['request'] = request
        document['state'] = "UNKNOWN"
        document['run_log'] = dict()
        document['task_logs'] = list()
        document['outputs'] = dict()

        # Return run document
        return(document)


    def insert_workflow_run(self, request, limit=None):
        '''Saves workflow run to database; returns unique run id'''

        # Initialize run document
        document = self.__init_run_document(request)

        # Unless a specified limit of entries is already available...
        if limit is None or self.collection.count() < limit:

            # Keep on trying until a unique run id was found and inserted
            while True:
                try:

                    # Create unique run id and add to document
                    document['run_id'] = self.__create_run_id()

                    # Try to insert
                    self.latest_object_id = self.collection.insert(document)

                    # Return run id
                    return document['run_id']

                except DuplicateKeyError:
                    continue
