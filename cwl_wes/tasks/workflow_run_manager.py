"""Workflow run manager executed on worker."""

from datetime import datetime
import logging
import os
import subprocess
import time
from typing import Dict, List, Optional

from foca.models.config import Config
from pymongo.errors import PyMongoError

from cwl_wes.tasks.cwl_log_processor import CWLLogProcessor, CWLTesProcessor
import cwl_wes.utils.db as db_utils
from cwl_wes.worker import celery_app

# Get logger instance
logger = logging.getLogger(__name__)


class WorkflowRunManager:  # pylint: disable=too-many-instance-attributes
    """Workflow run manager."""

    def __init__(
        self,
        command_list: List,
        task: celery_app.Task,
        tmp_dir: str,
        token: Optional[str] = None,
    ) -> None:
        """Initiate workflow run manager instance.

        Args:
            task: Celery task instance for initiating workflow run.
            task_id: Unique identifier for workflow run task.
            command_list: List of commands to be executed as a part of workflow
                run.
            tmp_dir: Current working directory to be passed for child process
                execution context.
            token: JSON Web Token (JWT).
            foca_config: :py:class:`foca.models.config.Config` instance
                describing configurations registered with `celery_app`.
            custom_config: :py:class:`cwl_wes.custom_config.CustomConfig`
                instance describing custom configuration model for cwl-WES
                specific configurations.
            collection: Collection client for saving task run progress.
            tes_config: TES (Task Execution Service) endpoint configurations.
            authorization: Boolean to define the security auth configuration
                for the app.
            string_format: String time format for task timestamps.

        Attributes:
            task: Celery task instance for initiating workflow run.
            task_id: Unique identifier for workflow run task.
            command_list: List of commands to be executed as a part of workflow
                run.
            tmp_dir: Current working directory to be passed for child process
                execution context.
            token: JSON Web Token (JWT).
            foca_config: :py:class:`foca.models.config.Config` instance
                describing configurations registered with `celery_app`.
            custom_config: :py:class:`cwl_wes.custom_config.CustomConfig`
                instance describing custom configuration model for cwl-WES
                specific configurations.
            collection: Collection client for saving task run progress.
            tes_config: TES (Task Execution Service) endpoint configurations.
            authorization: Boolean to define the security auth configuration
                for the app.
            string_format: String time format for task timestamps.
        """
        self.task = task
        self.task_id = self.task.request.id
        self.command_list = command_list
        self.tmp_dir = tmp_dir
        self.token = token
        self.foca_config: Config = celery_app.conf.foca
        self.controller_config = self.foca_config.custom.controller
        self.collection = (
            self.foca_config.db.dbs["cwl-wes-db"].collections["runs"].client
        )
        self.tes_config = {
            "url": self.controller_config.tes_server.url,
            "query_params": (
                self.controller_config.tes_server.status_query_params
            ),
            "timeout": self.controller_config.tes_server.timeout,
        }
        self.authorization = self.foca_config.security.auth.required
        self.string_format: str = "%Y-%m-%d %H:%M:%S.%f"

    def trigger_task_start_events(self) -> None:
        """Trigger task start events."""
        if not self.collection.find_one({"task_id": self.task.request.id}):
            return
        internal = {}
        current_ts = time.time()
        internal["task_started"] = datetime.utcfromtimestamp(current_ts)
        # Update run document in database
        try:
            self.update_run_document(
                state="RUNNING",
                internal=internal,
                task_started=datetime.utcfromtimestamp(current_ts).strftime(
                    self.string_format
                ),
            )
        except PyMongoError as exc:
            logger.exception(
                "Database error. Could not update log information for task"
                f" '{self.task_id}'. Original error message:"
                f" {type(exc).__name__}: {exc}"
            )
            raise

    def trigger_task_failure_events(self, task_end_ts):
        """Trigger task failure events.

        Args:
            task_end_ts: Task end timestamp.
        """
        if not self.collection.find_one({"task_id": self.task_id}):
            return

        # Create dictionary for internal parameters
        internal = {}
        internal["task_finished"] = datetime.utcfromtimestamp(task_end_ts)
        task_meta_data = celery_app.AsyncResult(id=self.task_id)
        internal["traceback"] = task_meta_data.traceback

        # Update run document in databse
        self.update_run_document(
            state="SYSTEM_ERROR",
            internal=internal,
            task_finished=datetime.utcfromtimestamp(task_end_ts).strftime(
                self.string_format
            ),
            exception=task_meta_data.result,
        )

    def trigger_task_success_events(  # pylint: disable=too-many-arguments
        self,
        returncode: int,
        log: str,
        tes_ids: List[str],
        token: str,
        task_end_ts: float,
    ) -> None:
        """Trigger task success events.

        Args:
            returncode: Task completion status code.
            log: Task run log.
            tes_ids: TES task identifiers.
            token: TES token.
            task_end_ts: Task end timestamp.
        """
        if not self.collection.find_one({"task_id": self.task_id}):
            return

        # Parse subprocess results
        log_list = log
        log = os.linesep.join(log)

        # Create dictionary for internal parameters
        internal = {}
        internal["task_finished"] = datetime.utcfromtimestamp(task_end_ts)

        # Set final state to be set
        document = self.collection.find_one(
            filter={"task_id": self.task_id},
            projection={
                "api.state": True,
                "_id": False,
            },
        )
        if document and document["api"]["state"] == "CANCELING":
            state = "CANCELED"
        elif returncode:
            state = "EXECUTOR_ERROR"
        else:
            state = "COMPLETE"

        # Extract run outputs
        cwl_tes_processor = CWLTesProcessor(tes_config=self.tes_config)
        outputs = cwl_tes_processor.cwl_tes_outputs_parser_list(log=log_list)

        # Get task logs
        task_logs = cwl_tes_processor.get_tes_task_logs(
            tes_ids=tes_ids,
            token=token,
        )

        # Update run document in database
        try:
            self.update_run_document(
                state=state,
                internal=internal,
                outputs=outputs,
                task_logs=task_logs,
                task_finished=datetime.utcfromtimestamp(task_end_ts).strftime(
                    self.string_format
                ),
                return_code=returncode,
                stdout=log,
                stderr="",
            )
        except PyMongoError as exc:
            logger.exception(
                "Database error. Could not update log information for task"
                f" '{self.task_id}'. Original error message:"
                f" {type(exc).__name__}: {exc}"
            )
            raise

    def trigger_task_end_events(
        self,
        returncode: int,
        log: str,
        tes_ids: List[str],
        token: str,
    ) -> None:
        """Trigger task completion events.

        Args:
            returncode: Task completion status code.
            log: Task run log.
            tes_ids: TES task identifiers.
            token: TES token.
            task_end_ts: Task end timestamp.
        """
        task_end_ts = time.time()
        if returncode == 0:
            self.trigger_task_success_events(
                log=log,
                tes_ids=tes_ids,
                token=token,
                task_end_ts=task_end_ts,
                returncode=returncode,
            )
        else:
            self.trigger_task_failure_events(task_end_ts=task_end_ts)

    def update_run_document(  # pylint: disable=too-many-branches
        self,
        state: Optional[str] = None,
        internal: Optional[Dict] = None,
        outputs: Optional[Dict] = None,
        task_logs: Optional[List[Dict]] = None,
        **run_log_params,
    ):
        """Update run document.

        Specifically, update state, internal and run log parameters in database
        document.

        Args:
            state: Task state.
            internal: Task specific internal parameters.
            outputs: Task specific output parameters.
            task_logs: Task run logs.
            **run_log_params: Run log parameters.
        """
        # TODO: Minimize db ops; try to compile entire object & update once
        # Update internal parameters
        if internal:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=self.task_id,
                root="internal",
                **internal,
            )

        # Update outputs
        if outputs:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=self.task_id,
                root="api.outputs",
                **outputs,
            )

        # Update task logs
        if task_logs:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=self.task_id,
                root="api",
                task_logs=task_logs,
            )

        # Update run log parameters
        if run_log_params:
            document = db_utils.upsert_fields_in_root_object(
                collection=self.collection,
                task_id=self.task_id,
                root="api.run_log",
                **run_log_params,
            )

        # Calculate queue, execution and run time
        if document and document["internal"]:
            run_log = document["internal"]
            durations = {}

            if "task_started" in run_log_params:
                if "task_started" in run_log and "task_received" in run_log:
                    durations["time_queue"] = (
                        run_log["task_started"] - run_log["task_received"]
                    ).total_seconds()

            if "task_finished" in run_log_params:
                if "task_finished" in run_log and "task_started" in run_log:
                    durations["time_execution"] = (
                        run_log["task_finished"] - run_log["task_started"]
                    ).total_seconds()
                if "task_finished" in run_log and "task_received" in run_log:
                    durations["time_total"] = (
                        run_log["task_finished"] - run_log["task_received"]
                    ).total_seconds()

            if durations:
                document = db_utils.upsert_fields_in_root_object(
                    collection=self.collection,
                    task_id=self.task_id,
                    root="api.run_log",
                    **durations,
                )

        # Update state
        if state:
            try:
                document = db_utils.update_run_state(
                    collection=self.collection,
                    task_id=self.task_id,
                    state=state,
                )
            except PyMongoError as exc:
                logger.exception(
                    "Database error. Could not update log information for task"
                    f" '{self.task_id}'. Original error message:"
                    f" {type(exc).__name__}: {exc}"
                )
                raise

        # Log info message
        if document:
            logger.info(
                f"State of run '{document['run_id']}' (task id:"
                f" '{self.task_id}') changed to '{state}'."
            )

        return document

    def run_workflow(self):
        """Initiate workflow run."""
        self.trigger_task_start_events()
        proc = subprocess.Popen(  # pylint: disable=consider-using-with
            self.command_list,
            cwd=self.tmp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        # Parse output in real-time
        cwl_log_processor = CWLLogProcessor(
            tes_config=self.tes_config, collection=self.collection
        )
        log, tes_ids = cwl_log_processor.process_cwl_logs(
            self.task,
            stream=proc.stdout,
            token=self.token,
        )
        returncode = proc.wait()
        self.trigger_task_end_events(
            token=self.token, returncode=returncode, log=log, tes_ids=tes_ids
        )
