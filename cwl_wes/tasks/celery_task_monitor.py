"""Celery task monitor, event handlers and related utility functions."""

from ast import literal_eval
from datetime import datetime
import logging
import os
import re
from shlex import quote
from threading import Thread
from time import sleep
from typing import (Dict, List, Optional)

from celery import Celery
from celery.events import Event
from celery.events.receiver import EventReceiver
from kombu.connection import Connection  # noqa: F401
from pymongo import collection as Collection
import tes

import cwl_wes.utils.db_utils as db_utils


# Get logger instance
logger = logging.getLogger(__name__)


# Set string time format
strf: str = '%Y-%m-%d %H:%M:%S.%f'


class TaskMonitor():
    """Celery task monitor."""

    def __init__(
        self,
        celery_app: Celery,
        collection: Collection,
        tes_config: Dict[str, str],
        timeout: float = 0,
        authorization: bool = True,
    ) -> None:
        """Starts Celery task monitor daemon process."""
        self.celery_app = celery_app
        self.collection = collection
        self.timeout = timeout
        self.authorization = authorization
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
        event: Event,
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

        # Build command
        if 'command_list' in kwargs:
            if self.authorization:
                kwargs['command_list'][3] = '<REDACTED>'
                kwargs['command_list'][5] = '<REDACTED>'
            command = ' '.join(
                [quote(item) for item in kwargs['command_list']]
            )
        else:
            command = 'N/A'

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_received'] = datetime.utcfromtimestamp(
            event['timestamp']
        )
        internal['process_id_worker'] = event['pid']
        internal['host'] = event['hostname']

        # Update run document in database
        try:
            self.update_run_document(
                event=event,
                state='QUEUED',
                internal=internal,
                task_received=datetime.utcfromtimestamp(
                    event['timestamp']
                ).strftime(strf),
                command=command,
                utc_offset=event['utcoffset'],
                max_retries=event['retries'],
                expires=event['expires'],
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
        event: Event,
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
                task_started=datetime.utcfromtimestamp(
                    event['timestamp']
                ).strftime(strf),
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
        event: Event,
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
            task_finished=datetime.utcfromtimestamp(
                event['timestamp']
            ).strftime(strf),
            exception=event['exception'],
        )

    def on_task_succeeded(
        self,
        event: Event,
    ) -> None:
        """Event handler for successful, failed and canceled Celery
        tasks."""
        if not self.collection.find_one({'task_id': event['uuid']}):
            return None
        # Parse subprocess results
        try:
            (returncode, log, tes_ids, token) = literal_eval(event['result'])
            log_list=log
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

        # Create dictionary for internal parameters
        internal = dict()
        internal['task_finished'] = datetime.utcfromtimestamp(
            event['timestamp']
        )

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
        #outputs = self.__cwl_tes_outputs_parser(log)
        outputs = self.__cwl_tes_outputs_parser_list(log_list)

        # Get task logs
        task_logs = self.__get_tes_task_logs(
            tes_ids=tes_ids,
            token=token,
        )

        # Update run document in database
        try:
            self.update_run_document(
                event=event,
                state=state,
                internal=internal,
                outputs=outputs,
                task_logs=task_logs,
                task_finished=datetime.utcfromtimestamp(
                    event['timestamp']
                ).strftime(strf),
                return_code=returncode,
                stdout=log,
                stderr='',
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
        event: Event,
    ) -> None:
        """Event handler for TES task state changes."""
        # If TES task is new, add task log to database
        if not event['tes_state']:
            tes_log = self.__get_tes_task_log(
                tes_id=event['tes_id'],
                token=event['token'],
            )
            try:
                db_utils.append_to_tes_task_logs(
                    collection=self.collection,
                    task_id=event['uuid'],
                    tes_log=tes_log,
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

        # Calculate queue, execution and run time
        if document and document['internal']:
            run_log = document['internal']
            durations = dict()

            if 'task_started' in run_log_params:
                if 'task_started' in run_log and 'task_received' in run_log:
                    pass
                    durations['time_queue'] = (
                        run_log['task_started'] - run_log['task_received']
                    ).total_seconds()

            if 'task_finished' in run_log_params:
                if 'task_finished' in run_log and 'task_started' in run_log:
                    pass
                    durations['time_execution'] = (
                        run_log['task_finished'] - run_log['task_started']
                    ).total_seconds()
                if 'task_finished' in run_log and 'task_received' in run_log:
                    pass
                    durations['time_total'] = (
                        run_log['task_finished'] - run_log['task_received']
                    ).total_seconds()

            if durations:
                document = db_utils.upsert_fields_in_root_object(
                    collection=self.collection,
                    task_id=event['uuid'],
                    root='api.run_log',
                    **durations,
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
        if document:
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
            r'(^\{$\n^ {4}"\S+": [\[\{]$\n(^ {4,}.*$\n)*^ {4}[\]\}]$\n^\}$\n)',
            re.MULTILINE
        )
        m = re_outputs.search(log)
        if m:
            return literal_eval(m.group(1))
        else:
            return dict()
    
    @staticmethod
    def __cwl_tes_outputs_parser_list(log: List) -> Dict:
        """This function parses outputs from the cwl-tes log"""
        """The outputs JSON starts at the line before last in the logs"""
        """So unless the outputs are empty ({}), parse upward,"""
        """until you find the beginning of the JSON containing the outputs"""
        
        indices=range(len(log)-1,-1,-1)

        start=-1
        end=-1
        for index in indices:
            if log[index].rstrip()=='{}':
                return dict()
            elif log[index].rstrip()=='}':
                end=index
                break
        
        # No valid JSON was found and the previous loop
        # reached the end of the log
        if end==0:
            return dict()
        
        indices=range(end-1,-1,-1)
        for index in indices:
            if log[index].rstrip()=='{':
                start=index
                break

        json=os.linesep.join(log[start:end+1])

        try:
            return literal_eval(json)
        except ValueError as verr:
            logger.exception(
                "ValueError when evaluation JSON: '%s'. Original error message: %s" % \
                   (json, verr)
            )
            return dict()
        except SyntaxError as serr:
            logger.exception(
                "SyntaxError when evaluation JSON: '%s'. Original error message: %s" % \
                    (json, serr)
            )
            return dict()

    def __get_tes_task_logs(
        self,
        tes_ids: List = list(),
        token: Optional[str] = None,
    ) -> List[Dict]:
        """Gets multiple task logs from TES instance."""
        task_logs = list()
        for tes_id in tes_ids:
            task_logs.append(
                self.__get_tes_task_log(
                    tes_id=tes_id,
                    token=token,
                )
            )
        return task_logs

    def __get_tes_task_log(
        self,
        tes_id: str,
        token: Optional[str] = None,
    ) -> Dict:
        """Gets task log from TES instance."""
        tes_client = tes.HTTPClient(
            url=self.tes_config['url'],
            timeout=self.tes_config['timeout'],
            token=token,
        )

        task_log = {}

        try:
            task_log = tes_client.get_task(
                task_id=tes_id,
                view=self.tes_config['query_params'],
            ).as_dict()
        except Exception as e:
            # TODO: handle more robustly: only 400/Bad Request is okay;
            # TODO: other errors (e.g. 500) should be dealt with
            logger.warning(
                "Could not obtain task log. Setting default. Original error "
                f"message: {type(e).__name__}: {e}"
            )
            task_log = {}

        logger.debug(f'Task log: {task_log}')

        return task_log
