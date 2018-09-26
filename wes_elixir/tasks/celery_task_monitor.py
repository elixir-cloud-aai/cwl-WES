from ast import literal_eval
from datetime import datetime
import logging
import os
from shlex import quote
from threading import Thread
from time import sleep

import wes_elixir.database.db_utils as db_utils


# Get logger instance
logger = logging.getLogger(__name__)


class TaskMonitor():
    '''Celery task monitor'''

    def __init__(self, celery_app, collection, timeout=0):
        '''Start Celery task monitor daemon process'''

        self.celery_app = celery_app
        self.collection = collection
        self.timeout = timeout

        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

        logger.debug("Celery task monitor daemon process started...")


    def run(self):
        '''Daemon process for Celery task monitor'''

        while True:

            try:

                with self.celery_app.connection() as connection:

                    listener = self.celery_app.events.Receiver(connection, handlers={
                        'task-failed'    : self.on_task_failed,
                        'task-received'  : self.on_task_received,
                        'task-revoked'   : self.on_task_revoked,
                        'task-started'   : self.on_task_started,
                        'task-succeeded' : self.on_task_succeeded
                    })
                    listener.capture(limit=None, timeout=None, wakeup=True)

            except (KeyboardInterrupt, SystemExit):
                raise

            except Exception as e:
                # TODO: implement better
                print(e)
                pass

            # Sleep for specified interval
            sleep(self.timeout)

        logger.warning("Celery task monitor daemon process shut down!")


    def update_run_document(
        self,
        event,
        state='UNKNOWN',
        internal=None,
        **run_log_params
    ):

        '''Update state, internal and run log parameters'''
        # TODO: Handle errors

        # Update internal parameters
        if not internal is None:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root="internal",
                **internal,
            )

        # Update run log parameters
        if run_log_params:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root="api.run_log",
                **run_log_params,
            )

        # Calculate queue, execution and run time

        if document['internal']:
            run_log = document['internal']
            durations = dict()

            if 'task_started' in run_log_params:
                if 'task_started' in run_log and 'task_received' in run_log:
                    pass
                    durations['time_queue'] = (run_log['task_started'] - run_log['task_received']).total_seconds()

            if 'task_finished' in run_log_params:
                if 'task_finished' in run_log and 'task_started' in run_log:
                    pass
                    durations['time_execution'] = (run_log['task_finished'] - run_log['task_started']).total_seconds()
                if 'task_finished' in run_log and 'task_received' in run_log:
                    pass
                    durations['time_total'] = (run_log['task_finished'] - run_log['task_received'] ).total_seconds()

            if durations:
                document = db_utils.upsert_fields_in_root_object(
                    collection=self.collection,
                    task_id=event['uuid'],
                    root="api.run_log",
                    **durations,
                )

        # Update state
        document = db_utils.update_run_state(
            collection=self.collection,
            task_id=event['uuid'],
            state=state,
        )

        # Log info message
        logger.info("State of run '{run_id}' (task id: {task_id}) changed to '{state}'".format(
            run_id=document['run_id'],
            task_id=event['uuid'],
            state=state,
        ))


    ### STATE: SYSTEM_ERROR ###
    def on_task_failed(self, event):

        '''Event handler for failed (system error) Celery tasks'''

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_finished'] = datetime.utcfromtimestamp(event['timestamp'])
        internal['traceback'] = event['traceback']

        # Update run document in databse
        self.update_run_document(
            event=event,
            state='SYSTEM_ERROR',
            internal=internal,
            task_finished=datetime.utcfromtimestamp(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f"),
            exception=event['exception'],
        )
        

    ### STATE: QUEUED ###
    def on_task_received(self, event):

        '''Event handler for received Celery tasks'''

        # Parse subprocess inputs
        kwargs = literal_eval(event['kwargs'])
        command = ' '.join([quote(item) for item in kwargs['command_list']])

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_received'] = datetime.utcfromtimestamp(event['timestamp'])
        internal['process_id'] = event['pid']
        internal['host'] = event['hostname']

        # Update run document in databse
        self.update_run_document(
            event=event,
            state='QUEUED',
            internal=internal,
            task_received=datetime.utcfromtimestamp(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f"),
            command=command,
            utc_offset=event['utcoffset'],
            max_retries=event['retries'],
            expires=event['expires'],
        )


    ### STATE: CANCELED ###
    def on_task_revoked(self, event):

        '''Event handler for revoked Celery tasks'''
        
        # Create dictionary for internal parameters
        internal = dict()
        internal['task_finished'] = datetime.utcfromtimestamp(event['timestamp'])
        internal['signal_number'] = event['signum']
        internal['terminated'] = event['terminated']

        # Update run document in databse
        self.update_run_document(
            event=event,
            state='CANCELED',
            internal=internal,
            task_finished=datetime.utcfromtimestamp(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f"),
            expired=event['expired'],
        )


    ### STATE: RUNNING ###
    def on_task_started(self, event):

        '''Event handler for started Celery tasks'''

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_started'] = datetime.utcfromtimestamp(event['timestamp'])

        # Update run document in databse
        self.update_run_document(
            event=event,
            state='RUNNING',
            internal=internal,
            task_started=datetime.utcfromtimestamp(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f"),
        )


    ### STATE: EXECUTOR_ERROR / COMPLETE ###
    def on_task_succeeded(self, event):

        '''Event handler for successful and failed (executor error) Celery tasks'''

        # Parse subprocess results
        result = literal_eval(event['result'])

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_finished'] = datetime.utcfromtimestamp(event['timestamp'])

        # Set state depending on return code
        if result['returncode']:
            state='EXECUTOR_ERROR'
        else:
            state='COMPLETE'

        # Update run document in databse
        self.update_run_document(
            event=event,
            state=state,
            internal=internal,
            task_finished=datetime.utcfromtimestamp(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f"),
            return_code=result['returncode'],
            stdout=os.linesep.join(result['stdout']),
            stderr=os.linesep.join(result['stderr']),
        )