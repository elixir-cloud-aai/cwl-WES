from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from random import choice
from services.db import PyMongoUtils


class Runs:

    def __init__(self, collection, index, run_id_length, run_id_charset, default_page_size, debug=False, dummy_request=None, limit=None):
        '''Instantiate ServiceInfo object'''

        # Set run mode and debug params
        self.debug = debug
        self.debug_limit = limit

        # Set collection and index field
        self.collection = collection
        self.index = index

        # Set run id generation parameters
        self.run_id_length = run_id_length
        self.run_id_charset = run_id_charset

        # Set default page size for run collection list
        self.default_page_size = default_page_size

        # Initialize service info object id
        self.latest_object_id = PyMongoUtils.find_id_latest(self.collection)

        # DEBUG: Save dummy workflow in database
        if self.debug:
            self.run_workflow(dummy_request, debug=True)


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


    def __run_workflow(self, document):
        '''Helper function for `run_workflow()`'''
        # TODO: implement logic & run in background
        pass


    def __cancel_run(self, run_id):
        '''Helper function for `cancel_run()`'''
        # TODO: implement logic & run in background (or not?)
        return run_id


    def cancel_run(self, run_id):
        '''Cancel running workflow'''

        # Cancel workflow run
        run_id = self.__cancel_run(run_id)

        # Return run_id
        return run_id


    def get_run_log(self, run_id):
        '''Get detailed log information for specific run'''
        return PyMongoUtils.find_one_by_index(self.collection, self.index, run_id)


    def get_run_status(self, run_id):
        '''Get status information for specific run'''
        return {
            "run_id": run_id,
            "state": PyMongoUtils.find_one_field_by_index(self.collection, self.index, run_id, 'state')
        }


    def list_runs(self, page_size=None):
        '''Get status information for specific run'''

        # TODO: stable ordering (newest last?)
        # TODO: implement next page token

        # Fall back to defaul page size if not provided by user
        if page_size is None:
            page_size = self.default_page_size

        # Query database for workflow runs
        cursor = PyMongoUtils.find_fields(self.collection, ['run_id', 'state'])

        # Iterate through list 
        runs_list = list()
        for record in cursor:
            runs_list.append(record)

        # Return formatted response object
        return {
            "next_page_token": "token",
            "runs": runs_list
        }


    def run_workflow(self, request, debug=False):
        '''Execute workflow and save info to database; returns unique run id'''

        # Initialize run document
        document = self.__init_run_document(request)

        # Unless a specified limit of entries is already available...
        if not debug or self.debug_limit is None or self.collection.count() < self.debug_limit:

            # Keep on trying until a unique run id was found and inserted
            while True:
                try:

                    # Create unique run id and add to document
                    document['run_id'] = self.__create_run_id()

                    # Try to insert
                    self.latest_object_id = self.collection.insert(document)

                    # Execute workflow (unless debug)
                    # TODO: run in background
                    if not debug:
                        self.__run_workflow(document)

                    # Return run id
                    return document['run_id']

                except DuplicateKeyError:
                    continue

        # Else return None
        return None
