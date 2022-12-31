"""Celery background task to start workflow run."""

import logging
from typing import (List, Optional, Tuple)

from cwl_wes.worker import celery_app
from cwl_wes.tasks.tasks.workflow_run_manager import WorkflowRunManager


# Get logger instance
logger = logging.getLogger(__name__)


@celery_app.task(
    name='tasks.run_workflow',
    bind=True,
    ignore_result=True,
    track_started=True
)
def task__run_workflow(
    self,
    command_list: List,
    tmp_dir: str,
    token: Optional[str] = None,
) -> Tuple[int, List[str], List[str], Optional[str]]:
    """Adds workflow run to task queue."""
    # Execute task in background
    workflow_run_manager = WorkflowRunManager(
        task=self,
        command_list=command_list,
        tmp_dir=tmp_dir,
        token=token
    )
    return_val = workflow_run_manager.run_workflow()
    return return_val
