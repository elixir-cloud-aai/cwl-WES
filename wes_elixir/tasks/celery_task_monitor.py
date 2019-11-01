"""Celery task monitor, event handlers and related utility functions."""

from ast import literal_eval
from datetime import datetime
import logging
import os
import re
import requests
from threading import Thread
from time import sleep
from typing import (Dict, List, Optional)

from celery import Celery
from celery.events import Event
from celery.events.receiver import EventReceiver
from kombu.connection import Connection  # noqa: F401
from pymongo import collection as Collection

import wes_elixir.database.db_utils as db_utils


# Get logger instance
logger = logging.getLogger(__name__)


class TaskMonitor():
    """Celery task monitor."""


    def __init__(
        self,
        celery_app: Celery,
        collection: Collection,
        tes_config: Dict[str, str],
        stdout_endpoint: Optional[str] = None,
        stderr_endpoint: Optional[str] = None,
        timeout: float = 0,
        authorization: bool = True,
        time_format: str = "%Y-%m-%dT%H:%M:%SZ",
    ) -> None:
        """Starts Celery task monitor daemon process."""
        self.celery_app = celery_app
        self.collection = collection
        self.stdout_endpoint = stdout_endpoint
        self.stderr_endpoint = stderr_endpoint
        self.timeout = timeout
        self.authorization = authorization
        self.time_format = time_format
        self.tes_config = tes_config

        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

        logger.debug('Celery task monitor daemon process started...')


    def run(self) -> None:
        """Daemon process for Celery task monitor."""
        while True:

            try:

                with self.celery_app.connection() as \
                     connection:  # type: Connection

                    listener: EventReceiver = self.celery_app.events.Receiver(
                        connection,
                        handlers={
                            'task-received':
                                self.on_task_received,
                            'task-started':
                                self.on_task_started,
                            'task-failed':
                                self.on_task_failed,
                            'task-succeeded':
                                self.on_task_succeeded,
                            'task-tes-task-update':
                                self.on_task_tes_task_update,
                        }
                    )
                    listener.capture(limit=None, timeout=None, wakeup=True)

            except KeyboardInterrupt as e:
                logger.exception(
                    (
                        'Task monitor interrupted. Execution aborted. '
                        'Original error message: {type}: {msg}'
                    ).format(
                        type=type(e).__name__,
                        msg=e,
                    )
                )
                raise SystemExit

            except Exception as e:
                logger.exception(
                    (
                        'Unknown error in task monitor occurred. Original '
                        'error message: {type}: {msg}'
                    ).format(
                        type=type(e).__name__,
                        msg=e,
                    )
                )
                pass

            # Sleep for specified interval
            sleep(self.timeout)


    def on_task_received(
        self,
        event: Event
    ) -> None:
        """Event handler for received Celery tasks."""
        if not event['name'] == 'tasks.run_workflow':
            return None
        # Parse subprocess inputs
        try:
            kwargs = literal_eval(event['kwargs'])
        except Exception as e:
            logger.exception(
                (
                    "Field 'kwargs' in event message malformed. Original "
                    'error message: {type}: {msg}'
                ).format(
                    type=type(e).__name__,
                    msg=e,
                )
            )
            pass

        # Process command
        if 'command_list' in kwargs:
            cmd = kwargs['command_list'][:]
            # Censor sensitive info
            try:
                cmd[cmd.index("--token") + 1] = '<REDACTED'
                cmd[cmd.index("--token-public-key") + 1] = '<REDACTED'
            except ValueError:
                pass
        else:
            cmd = []

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_received'] = datetime.utcfromtimestamp(
            event['timestamp']
        )
        internal['process_id_worker'] = event['pid']
        internal['host'] = event['hostname']
        internal['utcoffset'] = event['utcoffset']
        internal['max_retries'] = event['retries']
        internal['expires'] = event['expires']

        # Update run document in database
        try:
            self.update_run_document(
                event=event,
                state='QUEUED',
                internal=internal,
                cmd=cmd,
            )
        except Exception as e:
            logger.exception(
                (
                    'Database error. Could not update log information for '
                    "task '{task}'. Original error message: {type}: {msg}"
                ).format(
                    task=event['uuid'],
                    type=type(e).__name__,
                    msg=e,
                )
            )


    def on_task_started(
        self,
        event: Event
    ) -> None:
        """Event handler for started Celery tasks."""
        if not self.collection.find_one({'task_id': event['uuid']}):
            return None
        internal = dict()
        internal['task_started'] = datetime.utcfromtimestamp(
            event['timestamp']
        )
        # Update run document in database
        try:
            self.update_run_document(
                event=event,
                state='RUNNING',
                internal=internal,
                start_time=internal['task_started'].strftime(self.time_format),
            )
        except Exception as e:
            logger.exception(
                (
                    'Database error. Could not update log information for '
                    "task '{task}'. Original error message: {type}: {msg}"
                ).format(
                    task=event['uuid'],
                    type=type(e).__name__,
                    msg=e,
                )
            )


    def on_task_failed(
        self,
        event: Event
    ) -> None:
        """Event handler for failed (system error) Celery tasks."""
        if not self.collection.find_one({'task_id': event['uuid']}):
            return None
        # Create dictionary for internal parameters
        internal = dict()
        internal['task_finished'] = datetime.utcfromtimestamp(
            event['timestamp']
        )
        internal['traceback'] = event['traceback']

        # Update run document in databse
        self.update_run_document(
            event=event,
            state='SYSTEM_ERROR',
            internal=internal,
            end_time=internal['task_finished'].strftime(self.time_format),
            exception=event['exception'],
        )


    def on_task_succeeded(
        self,
        event: Event
    ) -> None:
        """Event handler for successful, failed and canceled Celery
        tasks."""
        document = self.collection.find_one({'task_id': event['uuid']})
        if not document:
            return None

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_finished'] = datetime.utcfromtimestamp(
            event['timestamp']
        )

        # Parse subprocess results
        try:
            (returncode, log, tes_ids) = literal_eval(event['result'])
            log = os.linesep.join(log)
        except Exception as e:
            logger.exception(
                (
                    "Field 'result' in event message malformed. Original "
                    'error message: {type}: {msg}'
                ).format(
                    type=type(e).__name__,
                    msg=e,
                )
            )
            pass

        # Save STDOUT & STDERR
        internal['stdout'] = log
        internal['stderr'] = ''

        # Compile API URLs to retreive STDOUT & STDERR
        if 'run_id' in document:
            if self.stdout_endpoint:
                stdout_url = '/'.join([self.stdout_endpoint, document['run_id']])
            else:
                stdout_url = 'unavailable'
            if self.stderr_endpoint:
                stderr_url = '/'.join([self.stderr_endpoint, document['run_id']])
            else:
                stderr_url = 'unavailable'

        # Set final state to be set
        document = self.collection.find_one(
            filter={'task_id': event['uuid']},
            projection={
                'api.state': True,
                '_id': False,
            }
        )
        if document and document['api']['state'] == 'CANCELING':
            state = 'CANCELED'
        elif returncode:
            state = 'EXECUTOR_ERROR'
        else:
            state = 'COMPLETE'

        # Extract run outputs
        outputs = self.__cwl_tes_outputs_parser(log)

        # Get task logs from TES
        internal['tes_logs'] = self.__get_tes_task_logs(tes_ids=tes_ids)

        # Process task logs
        task_logs = []
        for task_log in internal['tes_logs']:
            task_logs.append(
                self.__TES_to_WES_task_log(
                    task_log=task_log,
                )
            )

        # Update run document in database
        try:
            self.update_run_document(
                event=event,
                state=state,
                internal=internal,
                outputs=outputs,
                task_logs=task_logs,
                end_time=internal['task_finished'].strftime(self.time_format),
                exit_code=returncode,
                stdout=stdout_url,
                stderr=stderr_url,
            )
        except Exception as e:
            logger.exception(
                (
                    'Database error. Could not update log information for '
                    "task '{task}'. Original error message: {type}: {msg}"
                ).format(
                    task=event['uuid'],
                    type=type(e).__name__,
                    msg=e,
                )
            )
            pass


    def on_task_tes_task_update(
        self,
        event: Event
    ) -> None:
        """Event handler for TES task state changes."""
        # If TES task is new, add task log to database
        if not event['tes_state']:
            try:
                tes_log = self.__get_tes_task_log(tes_id=event['tes_id'])
                db_utils.append_to_tes_task_logs(
                    collection=self.collection,
                    task_id=event['uuid'],
                    task_log=tes_log,
                )
                wes_log = self.__TES_to_WES_task_log(task_log=tes_log)
                db_utils.append_to_wes_task_logs(
                    collection=self.collection,
                    task_id=event['uuid'],
                    task_log=wes_log,
                )
                
            except Exception as e:
                logger.exception(
                    (
                        'Database error. Could not update log information for '
                        "task '{task}'. Original error message: {type}: {msg}"
                    ).format(
                        task=event['uuid'],
                        type=type(e).__name__,
                        msg=e,
                    )
                )
                pass

        # Otherwise only update state
        else:
            try:
                db_utils.update_tes_task_state(
                    collection=self.collection,
                    task_id=event['uuid'],
                    tes_id=event['tes_id'],
                    state=event['tes_state'],
                )
                logger.info(
                    (
                        "State of TES task '{tes_id}' of run with task ID "
                        "'{task_id}' changed to '{state}'."
                    ).format(
                        task_id=event['uuid'],
                        tes_id=event['tes_id'],
                        state=event['tes_state'],
                    )
                )
            except Exception as e:
                logger.exception(
                    (
                        'Database error. Could not update log information for '
                        "task '{task}'. Original error message: {type}: {msg}"
                    ).format(
                        task=event['uuid'],
                        type=type(e).__name__,
                        msg=e,
                    )
                )
                pass


    def update_run_document(
        self,
        event: Event,
        state: Optional[str] = None,
        internal: Optional[Dict] = None,
        outputs: Optional[Dict] = None,
        task_logs: Optional[List[Dict]] = None,
        **run_log_params
    ):
        """Updates state, internal and run log parameters in database
        document.
        """
        # TODO: Minimize db ops; try to compile entire object & update once
        # Update internal parameters
        if internal:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root='internal',
                **internal,
            )

        # Update outputs
        if outputs:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root='api.outputs',
                **outputs,
            )

        # Update task logs
        if task_logs:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root='api',
                task_logs=task_logs,
            )

        # Update run log parameters
        if run_log_params:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=event['uuid'],
                root='api.run_log',
                **run_log_params,
            )
        else:
            document = dict()

        # Calculate queue, execution and run time
        if 'internal' in document:
            run_log = document['internal']

            if 'task_started' in run_log_params:
                if 'task_started' in run_log and 'task_received' in run_log:
                    pass
                    run_log['time_queue'] = (
                        run_log['task_started'] - run_log['task_received']
                    ).total_seconds()

            if 'task_finished' in run_log_params:
                if 'task_finished' in run_log and 'task_started' in run_log:
                    pass
                    run_log['time_execution'] = (
                        run_log['task_finished'] - run_log['task_started']
                    ).total_seconds()
                if 'task_finished' in run_log and 'task_received' in run_log:
                    pass
                    run_log['time_total'] = (
                        run_log['task_finished'] - run_log['task_received']
                    ).total_seconds()

                document = db_utils.upsert_fields_in_root_object(
                    collection=self.collection,
                    task_id=event['uuid'],
                    root='api.run_log',
                    internal=internal,
                )

        # Update state
        if state:
            try:
                document = db_utils.update_run_state(
                    collection=self.collection,
                    task_id=event['uuid'],
                    state=state,
                )
            except Exception:
                raise

        # Log info message
        if 'run_id' in document:
            logger.info(
                (
                    "State of run '{run_id}' (task id: '{task_id}') changed "
                    "to '{state}'."
                ).format(
                    run_id=document['run_id'],
                    task_id=event['uuid'],
                    state=state,
                )
            )

        return document


    @staticmethod
    def __cwl_tes_outputs_parser(log: str) -> Dict:
        """Parses outputs from cwl-tes log."""
        # Find outputs object in log string
        re_outputs = re.compile(
            r'(^\{$\n^ {4}"\S+": \{$\n(^ {4,}.*$\n)*^ {4}\}$\n^\}$\n)',
            re.MULTILINE
        )
        m = re_outputs.search(log)
        if m:
            return literal_eval(m.group(1))
        else:
            return dict()


    def __get_tes_task_logs(
        self,
        tes_ids: List = list()
    ) -> List:
        """Gets multiple task logs from TES instance."""
        task_logs = list()
        for tes_id in tes_ids:
            task_logs.append(self.__get_tes_task_log(tes_id))
        return task_logs


    def __get_tes_task_log(
        self,
        tes_id: str
    ) -> Dict:
        """Gets task log from TES instance."""
        # Build URL
        base = self.tes_config['url']
        root = self.tes_config['logs_endpoint_root']
        suffix = ''.join(
            [tes_id, self.tes_config['logs_endpoint_query_params']]
        )
        url = '/'.join(frag.strip('/') for frag in [base, root, suffix])

        # Send GET request to URL to obtain task log
        task_log = requests.get(url).json()

        return task_log


    @staticmethod
    def __TES_to_WES_task_log(
        task_log: Dict,
        index: int = 0,
    ) -> Dict:
        """
        Converts TES task info/log to WES-compliant task log.

        Unavailable properties are not set.

        As invididual TES logs currently may return multiple commands for most
        properties, but WES logs expect only a single value, only the value in
        each array is returned that corresponds to the specified index.
        """
        wes_task_log: Dict = dict()

        # Set task name
        try:
            wes_task_log['name'] = task_log['name']
        except KeyError:
            pass
        
        # Set task start time
        try:
            wes_task_log['start_time'] = task_log['logs'][index]['start_time']
        except (KeyError, TypeError):
            pass
        
        # Set task end time
        try:
            wes_task_log['end_time'] = task_log['logs'][index]['end_time']
        except (KeyError, TypeError):
            pass

        # Set task exit code
        try:
            wes_task_log['exit_code'] = \
                task_log['logs'][index]['logs'][index]['exit_code']
        except (IndexError, KeyError, TypeError):
            pass
        
        # Set task command
        try:
            wes_task_log['cmd'] = task_log['executors'][index]['command']
        except (IndexError, KeyError, TypeError):
            pass
        
        # Set task STDOUT
        try:
            wes_task_log['stdout'] = task_log['executors'][index]['stdout']
        except (IndexError, KeyError, TypeError):
            pass
        
        # Set task STDERR
        try:
            wes_task_log['stderr'] = task_log['executors'][index]['stderr']
        except (IndexError, KeyError, TypeError):
            pass
        
        return wes_task_log
