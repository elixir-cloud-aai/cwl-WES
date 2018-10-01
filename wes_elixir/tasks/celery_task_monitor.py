from ast import literal_eval
from datetime import datetime
import json
import logging
import os
import re
import requests
from shlex import quote
import traceback
from threading import Thread
from time import sleep

import wes_elixir.database.db_utils as db_utils


# Get logger instance
logger = logging.getLogger(__name__)


class TaskMonitor():
    '''Celery task monitor'''

    def __init__(
        self,
        celery_app=None,
        collection=None,
        timeout=0,
        authorization=True,
        tes=None,
    ):

        '''Start Celery task monitor daemon process'''

        self.celery_app = celery_app
        self.collection = collection
        self.timeout = timeout
        self.authorization = authorization
        self.tes = tes

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

            except KeyboardInterrupt as e:
                logger.critical("Task monitor interrupted. Execution aborted. Original error message: {type}: {msg}".format(
                    type=type(e).__name__,
                    msg=e,
                ))
                raise SystemExit

            except Exception as e:
                logger.exception("Unknown error in task monitor occurred. Execution aborted.")
                raise SystemExit

            # Sleep for specified interval
            sleep(self.timeout)


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
        try:
            kwargs = literal_eval(event['kwargs'])
        except Exception:
            logger.exception("Field 'kwargs' in event message malformed. Execution aborted. Original error message:")
            raise SystemExit

        # Build command
        if 'command_list' in kwargs:
            if self.authorization: 
                kwargs['command_list'][3] = kwargs['command_list'][5] = '<REDACTED>'
            command = ' '.join([quote(item) for item in kwargs['command_list']])
        else:
            command = 'N/A'

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_received'] = datetime.utcfromtimestamp(event['timestamp'])
        internal['process_id'] = event['pid']
        internal['host'] = event['hostname']

        # Update run document in database
        try:
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
        except Exception as e:
            logger.error("Database error. Could not update log information for task {task}. Original error message: {type}: {msg}".format(
                task=event['uuid'],
                type=type(e).__name__,
                msg=e,
            ))
            pass


    ### STATE: CANCELED ###
    def on_task_revoked(self, event):

        '''Event handler for revoked Celery tasks'''

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_finished'] = datetime.utcfromtimestamp(event['timestamp'])
        internal['signal_number'] = event['signum']
        internal['terminated'] = event['terminated']

        # Update run document in database
        try:
            self.update_run_document(
                event=event,
                state='CANCELED',
                internal=internal,
                task_finished=datetime.utcfromtimestamp(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f"),
                expired=event['expired'],
            )
        except Exception as e:
            logger.error("Database error. Could not update log information for task {task}. Original error message: {type}: {msg}".format(
                task=event['uuid'],
                type=type(e).__name__,
                msg=e,
            ))
            pass


    ### STATE: RUNNING ###
    def on_task_started(self, event):

        '''Event handler for started Celery tasks'''

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_started'] = datetime.utcfromtimestamp(event['timestamp'])

        # Update run document in database
        try:
            self.update_run_document(
                event=event,
                state='RUNNING',
                internal=internal,
                task_started=datetime.utcfromtimestamp(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f"),
            )
        except Exception as e:
            logger.error("Database error. Could not update log information for task {task}. Original error message: {type}: {msg}".format(
                task=event['uuid'],
                type=type(e).__name__,
                msg=e,
            ))
            pass


    ### STATE: EXECUTOR_ERROR / COMPLETE ###
    def on_task_succeeded(self, event):

        '''Event handler for successful and failed (executor error) Celery tasks'''

        # Parse subprocess results
        # NOTE: Hack to get around serialization/deserialization problem
        try:
            (returncode, stdout, stderr) = event['result'].strip('\'').split('<<<newfield>>>')
            returncode = int(returncode.strip('\''))
            stdout = stdout.strip('\'').split('<<<newline>>>')
            stderr = stderr.strip('\'').split('<<<newline>>>')
        except Exception:
            logger.exception("Field 'result' in event message malformed. Execution aborted. Original error message:")
            raise SystemExit

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_finished'] = datetime.utcfromtimestamp(event['timestamp'])

        # Set state depending on return code
        if returncode:
            state='EXECUTOR_ERROR'
        else:
            state='COMPLETE'

        # Extract run outputs
        outputs = self.__cwl_tes_outputs_parser(stdout)

        # Get task logs
        task_logs = self.__get_task_logs(stderr)

        # Update run document in database
        try:
            self.update_run_document(
                event=event,
                state=state,
                internal=internal,
                outputs=outputs,
                task_logs=task_logs,
                task_finished=datetime.utcfromtimestamp(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f"),
                return_code=returncode,
                stdout=os.linesep.join(stdout),
                stderr=os.linesep.join(stderr),
            )
        except Exception as e:
            logger.error("Database error. Could not update log information for task {task}. Original error message: {type}: {msg}".format(
                task=event['uuid'],
                type=type(e).__name__,
                msg=e,
            ))
            pass


    def update_run_document(
        self,
        event,
        state='UNKNOWN',
        internal=None,
        outputs=None,
        task_logs=None,
        **run_log_params
    ):

        '''Update state, internal and run log parameters'''

        # TODO: Minimize db ops; try to compile entire object & update once

        # Update internal parameters
        if internal:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root="internal",
                **internal,
            )

        # Update outputs
        if outputs:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root="api.outputs",
                **outputs,
            )

        # Update task logs
        if task_logs:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root="api",
                task_logs=task_logs,
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
        try:
            document = db_utils.update_run_state(
                collection=self.collection,
                task_id=event['uuid'],
                state=state,
            )
        except Exception:
            raise

        # Log info message
        logger.info("State of run '{run_id}' (task id: {task_id}) changed to '{state}'".format(
            run_id=document['run_id'],
            task_id=event['uuid'],
            state=state,
        ))


    @staticmethod
    def __cwl_tes_outputs_parser(lines):

        '''Parse outputs from CWL-TES log'''

        # Convert block to dictionary
        return literal_eval('\n'.join(lines))


    def __get_task_logs(
        self,
        lines=None
    ):

        '''Parse task IDs from CWL-TES log and get logs from TES instance'''

        # Set regular expressions
        re_task = re.compile(r"^\[job\s\w*?\]\stask\sid:\s(\S*)\s*$")

        # Set parameters
        tasks = list()
        task_logs = list()

        # Iterate over lines
        for line in lines:

            # Extract task ID when regex matches
            m = re_task.match(line)
            if m:
                tasks.append(m.group(1))

        # Iterate over task IDs
        for task_id in tasks:

            # Build URL
            base = self.tes['url']
            root = self.tes['logs_endpoint_root']
            suffix = self.tes['logs_endpoint_query_params']
            url = ''.join([base, root, task_id, suffix])

            # Send GET request to URL
            r = requests.get(url)

            # Add log to container
            task_logs.append(r.json())

        # Return task logs container
        return task_logs
