from datetime import datetime, timezone
from json import decoder, loads
from pymongo.errors import DuplicateKeyError
from random import choice
from services.db import PyMongoUtils
from services.error_handling.custom_errors import BadRequest, WorkflowNotFound
from services.utils import ServerUtils


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

        # Initialize workflow attachments
        self.workflow_attachment = None

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


    def __validate_run_request(self, form_data):
        '''Validate presence and types of workflow run request form data; sets defaults for optional'''

        # The form data is not validated properly because all types except 'workflow_attachment' are string and none are labeled as required
        # Considering the 'RunRequest' model in the current specs (0.3.0), the following assumptions are made and verified for the indicated parameters:
        # workflow_params:
        #   type: dict
        #   required: True
        # workflow_type:
        #   type: str
        #   required: True
        # workflow_type_version:
        #   type: str
        #   required: True
        # tags:
        #   type: dict
        #   required: False
        # workflow_engine_parameters:
        #   type: dict
        #   required: False
        # workflow_url:
        #   type: str
        #   required: True 
        # workflow_attachment:
        #   type: 
        #   required: False

        # Set required parameters
        required = {'workflow_params', 'workflow_type', 'workflow_type_version', 'workflow_url'}
        type_str = dict((key, form_data[key]) for key in ['workflow_type', 'workflow_type_version', 'workflow_url'] if key in form_data)
        type_dict = dict((key, form_data[key]) for key in ['workflow_params', 'workflow_engine_parameters', 'tags'] if key in form_data)
        # TODO: implement type casting/checking for workflow attachment

        # Raise error if any required params are missing
        if not required <= set(form_data):
            raise BadRequest()

        # Raise error if any string params are not of type string
        if not all(isinstance(value, str) for value in type_str.values()):
            raise BadRequest()

        # Raise error if any dict params are not of type dict
        if not all(isinstance(value, dict) for value in type_dict.values()):
            raise BadRequest()


    def __manage_workflow_attachments(self, form_data):
        '''Extract workflow attachments from form data'''

        # Extract workflow attachments from form data dictionary
        if 'workflow_attachment' in form_data:

            # TODO: do something with form_data['workflow_attachment']

            # Strip workflow attachments from form data
            del form_data['workflow_attachment']

        # Return form data stripped of workflow attachments
        return form_data


    def __run_workflow(self, document):
        '''Helper function for `run_workflow()`'''
        # TODO: implement logic & run in background
        pass


    def __cancel_run(self, run_id):
        '''Helper function for `cancel_run()`'''
        # TODO: implement logic
        return run_id


    def cancel_run(self, run_id):
        '''Cancel running workflow'''

        # Get workflow run state        
        state = PyMongoUtils.find_one_field_by_index(self.collection, self.index, run_id, 'state')

        # Raise error if workflow run was not found
        if state is None:
            raise WorkflowNotFound

        # Cancel workflow run
        run_id = self.__cancel_run(run_id)

        # Return run_id
        return run_id


    def get_run_log(self, run_id):
        '''Get detailed log information for specific run'''

        # Get worklow run log
        response = PyMongoUtils.find_one_by_index(self.collection, self.index, run_id)

        # Raise error if workflow run was not found
        if response is None:
            raise WorkflowNotFound

        # Return response
        return response


    def get_run_status(self, run_id):
        '''Get status information for specific run'''

        # Get workflow run state        
        state = PyMongoUtils.find_one_field_by_index(self.collection, self.index, run_id, 'state')

        # Raise error if workflow run was not found
        if state is None:
            raise WorkflowNotFound

        # Return response
        return {
            "run_id": run_id,
            "state": state
        }


    def list_runs(self, **kwargs):
        '''Get status information for specific run'''

        # TODO: stable ordering (newest last?)
        # TODO: implement next page token

        # Fall back to default page size if not provided by user
        page_size = kwargs['page_size'] if 'page_size' in kwargs else self.default_page_size

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


    def run_workflow(self, form_data, debug=False):
        '''Execute workflow and save info to database; returns unique run id'''

        # Format request
        if not debug:

            # Convert ImmutableMultiDict to nested dictionary
            form_data = ServerUtils.immutable_multi_dict_to_nested_dict(form_data)

            # Validate workflow run request
            self.__validate_run_request(form_data)

            # Handle workflow attachments
            form_data = self.__manage_workflow_attachments(form_data)

        # Initialize run document
        document = self.__init_run_document(form_data)

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
