"""cwl-tes log parser executed on worker."""

from ast import literal_eval
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from _io import TextIOWrapper
from pymongo.errors import PyMongoError
import tes

import cwl_wes.utils.db as db_utils
from cwl_wes.worker import celery_app

# Get logger instance
logger = logging.getLogger(__name__)


class CWLLogProcessor:
    """cwl-tes log parser executed on worker.

    Args:
        tes_config: TES configuration.
        collection: MongoDB collection.

    Attributes:
        tes_config: TES configuration.
        collection: MongoDB collection.
    """

    def __init__(self, tes_config, collection) -> None:
        """Construct class instance."""
        self.tes_config = tes_config
        self.collection = collection

    def process_cwl_logs(
        self,
        task: celery_app.Task,
        stream: TextIOWrapper,
        token: Optional[str] = None,
    ) -> Tuple[List, List]:
        """Parse cwl-tes logs.

        Args:
            task: Celery task instance.
            stream: Combined STDOUT/STDERR stream.
            token: OAuth2 token.

        Returns:
            Tuple of lists containing the following:
                - List of log lines.
                - List of TES task IDs.
        """
        stream_container: List = []
        tes_states: Dict = {}

        # Iterate over STDOUT/STDERR stream
        for line in iter(stream.readline, ""):

            line = line.rstrip()

            # Replace single quote characters to avoid `literal_eval()` errors
            line = line.replace("'", '"')

            # Handle special cases
            lines = self.process_tes_log(line)
            for processed_line in lines:
                stream_container.append(processed_line)
                logger.info(f"[{task}] {processed_line}")
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
        """Handle irregularities arising from log parsing.

        Args:
            line: Log line.

        Returns:
            List of log lines.
        """
        lines: List = []

        # Handle special case where FTP and cwl-tes logs are on same line
        re_ftp_cwl_tes = re.compile(
            r"^(\*cmd\* .*)(\[step \w*\] produced output \{)$"
        )
        match = re_ftp_cwl_tes.match(line)
        if match:
            lines.append(match.group(1))

        return lines

    def extract_tes_state(
        self,
        line: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract task ID and state from cwl-tes log.

        Args:
            line: Log line.

        Returns:
            Tuple of task ID and state.
        """
        task_id: Optional[str] = None
        task_state: Optional[str] = None

        # Extract new task ID
        re_task_new = re.compile(r"^\[job [\w\-]*\] task id: (\S*)$")
        match = re_task_new.match(line)
        if match:
            task_id = match.group(1)

        # Extract task ID and state
        re_task_state_poll = re.compile(
            r'^\[job [\w\-]*\] POLLING "(\S*)", result: (\w*)'
        )
        match = re_task_state_poll.match(line)
        if match:
            task_id = match.group(1)
            task_state = match.group(2)

        return (task_id, task_state)

    def capture_tes_task_update(
        self,
        task: celery_app.Task,
        tes_id: str,
        tes_state: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        """Handle TES task state change events.

        Args:
            task: Celery task instance.
            tes_id: TES task ID.
            tes_state: TES task state.
            token: OAuth2 token.
        """
        # If TES task is new, add task log to database
        logger.info(f"TES_STATE------------->{tes_state}")
        cwl_tes_processor = CWLTesProcessor(tes_config=self.tes_config)
        if not tes_state:
            tes_log = cwl_tes_processor.get_tes_task_log(
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
            except PyMongoError as exc:
                logger.exception(
                    "Database error. Could not update log information for"
                    f" task '{task.task_id}'. Original error message:"
                    f" {type(exc).__name__}: {exc}"
                )

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
                    f"State of TES task '{tes_id}' of run with task ID "
                    f"'{task.task_id}' changed to '{tes_state}'."
                )
            except PyMongoError as exc:
                logger.exception(
                    "Database error. Could not update log information for"
                    f" task '{task.task_id}'. Original error message:"
                    f" {type(exc).__name__}: {exc}"
                )


class CWLTesProcessor:
    """Class for processing cwl-tes logs.

    Args:
        tes_config: TES configuration.

    Attributes:
        tes_config: TES configuration.
    """

    def __init__(self, tes_config) -> None:
        """Construct class instance."""
        self.tes_config = tes_config

    @staticmethod
    def cwl_tes_outputs_parser(log: str) -> Dict:
        """Parse outputs from cwl-tes log.

        Args:
            log: cwl-tes log.

        Returns:
            Outputs dictionary.
        """
        re_outputs = re.compile(
            r'(^\{$\n^ {4}"\S+": [\[\{]$\n(^ {4,}.*$\n)*^ {4}[\]\}]$\n^\}$\n)',
            re.MULTILINE,
        )
        match = re_outputs.search(log)
        if match:
            return literal_eval(match.group(1))
        return {}

    @staticmethod
    def cwl_tes_outputs_parser_list(log: List) -> Dict:
        """Parse outputs from cwl-tes log.

        The outputs JSON starts at the line before last in the logs. So unless
        the outputs are empty ({}), parse upward, until you find the beginning
        of the JSON containing the outputs.

        Args:
            log: cwl-tes log.

        Returns:
            Outputs dictionary.
        """
        indices = range(len(log) - 1, -1, -1)

        start = -1
        end = -1
        for index in indices:
            if log[index].rstrip() == "{}":
                return {}
            if log[index].rstrip() == "}":
                end = index
                break

        # No valid JSON was found and the previous loop
        # reached the end of the log
        if end == 0:
            return {}

        indices = range(end - 1, -1, -1)
        for index in indices:
            if log[index].rstrip() == "{":
                start = index
                break

        json = os.linesep.join(log[start : end + 1])  # noqa: E203

        try:
            return literal_eval(json)
        except ValueError as exc:
            logger.exception(
                f"ValueError when evaluation JSON: {json}. Original error"
                f" message: {exc}"
            )
            return {}
        except SyntaxError as exc:
            logger.exception(
                f"SyntaxError when evaluation JSON: {json}. Original error"
                f" message: {exc}"
            )
            return {}

    def get_tes_task_logs(
        self,
        tes_ids: List,
        token: Optional[str] = None,
    ) -> List[Dict]:
        """Get multiple task logs from TES instance.

        Args:
            tes_ids: TES task IDs.
            token: OAuth2 token.

        Returns:
            Task logs.
        """
        task_logs = []
        for tes_id in tes_ids:
            task_logs.append(
                self.get_tes_task_log(
                    tes_id=tes_id,
                    token=token,
                )
            )
        return task_logs

    def get_tes_task_log(
        self,
        tes_id: str,
        token: Optional[str] = None,
    ) -> Dict:
        """Get single task log from TES instance.

        Args:
            tes_id: TES task ID.
            token: OAuth2 token.

        Returns:
            Task log.
        """
        tes_client = tes.HTTPClient(
            url=self.tes_config["url"],
            timeout=self.tes_config["timeout"],
            token=token,
        )

        task_log = {}

        try:
            task_log = tes_client.get_task(
                task_id=tes_id,
                view=self.tes_config["query_params"],
            ).as_dict()
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning(
                "Could not obtain task log. Setting default. Original error "
                f"message: {type(exc).__name__}: {exc}"
            )
            task_log = {}

        logger.debug(f"Task log: {task_log}")

        return task_log
