import re
import os
import logging
from _io import TextIOWrapper
from typing import (Dict, List, Optional, Tuple)
from ast import literal_eval

import tes
from cwl_wes.worker import celery_app
import cwl_wes.utils.db_utils as db_utils

# Get logger instance
logger = logging.getLogger(__name__)


class CWLLogProcessor:

    def __init__(self, tes_config, collection) -> None:
        self.tes_config = tes_config
        self.collection = collection
    
    def process_cwl_logs(
        self,
        task: celery_app.Task,
        stream: TextIOWrapper,
        token: Optional[str] = None,
    ) -> Tuple[List, List]:
        """Parses combinend cwl-tes STDOUT/STDERR and sends TES task IDs and state
        updates to broker."""
        stream_container: List = list()
        tes_states: Dict = dict()

        # Iterate over STDOUT/STDERR stream
        for line in iter(stream.readline, ''):

            line = line.rstrip()

            # Replace single quote characters to avoid `literal_eval()` errors
            line = line.replace("'", '"')

            # Handle special cases
            lines = self.process_tes_log(line)
            for line in lines:
                stream_container.append(line)
                logger.info(f"[{task}] {line}")
                continue

            # Detect TES task state changes
            (tes_id, tes_state) = self.extract_tes_state(line)
            if tes_id:

                # Handle new task
                if tes_id not in tes_states:
                    tes_states[tes_id] = tes_state
                    self.capture_tes_task_update(
                        task,
                        tes_id=tes_id,
                        token=token,
                    )
                # Handle state change
                elif tes_states[tes_id] != tes_state:
                    tes_states[tes_id] = tes_state
                    self.capture_tes_task_update(
                        task,
                        tes_id=tes_id,
                        tes_state=tes_state,
                    )
                logger.info(line)
                continue

            stream_container.append(line)
            logger.info(line)

        return (stream_container, list(tes_states.keys()))


    def process_tes_log(self, line: str) -> List[str]:
        """Handles irregularities arising from log parsing."""
        lines: List = list()

        # Handle special case where FTP and cwl-tes logs are on same line
        re_ftp_cwl_tes = re.compile(
            r'^(\*cmd\* .*)(\[step \w*\] produced output \{)$'
        )
        m = re_ftp_cwl_tes.match(line)
        if m:
            lines.append(m.group(1))

        return lines

    def extract_tes_state(
        self,
        line: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extracts task ID and state from cwl-tes log."""
        task_id: Optional[str] = None
        task_state: Optional[str] = None

        # Extract new task ID
        re_task_new = re.compile(r"^\[job [\w\-]*\] task id: (\S*)$")
        m = re_task_new.match(line)
        if m:
            task_id = m.group(1)

        # Extract task ID and state
        re_task_state_poll = re.compile(
            r'^\[job [\w\-]*\] POLLING "(\S*)", result: (\w*)'
        )
        m = re_task_state_poll.match(line)
        if m:
            task_id = m.group(1)
            task_state = m.group(2)

        return (task_id, task_state)


    def capture_tes_task_update(
        self,
        task: celery_app.Task,
        tes_id: str,
        tes_state: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        """Event handler for TES task state changes."""
        # If TES task is new, add task log to database
        logger.info(f"TES_STATE------------->{tes_state}")
        cwl_tes_processor = CWLTesProcessor(tes_config=self.tes_config)
        if not tes_state:
            tes_log = cwl_tes_processor.__get_tes_task_log(
                tes_id=tes_id,
                token=token,
            )
            logger.info(f"LOG------------->{tes_log}")
            try:
                db_utils.append_to_tes_task_logs(
                    collection=self.collection,
                    task_id=task.task_id,
                    tes_log=tes_log,
                )
            except Exception as e:
                logger.exception(
                    (
                        'Database error. Could not update log information for '
                        "task '{task}'. Original error message: {type}: {msg}"
                    ).format(
                        task=task.task_id,
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
                    task_id=task.task_id,
                    tes_id=tes_id,
                    state=tes_state,
                )
                logger.info(
                    (
                        "State of TES task '{tes_id}' of run with task ID "
                        "'{task_id}' changed to '{state}'."
                    ).format(
                        task_id=task.task_id,
                        tes_id=tes_id,
                        state=tes_state,
                    )
                )
            except Exception as e:
                logger.exception(
                    (
                        'Database error. Could not update log information for '
                        "task '{task}'. Original error message: {type}: {msg}"
                    ).format(
                        task=task.task_id,
                        type=type(e).__name__,
                        msg=e,
                    )
                )
                pass


class CWLTesProcessor:

    def __init__(self, tes_config) -> None:
        self.tes_config = tes_config
    
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