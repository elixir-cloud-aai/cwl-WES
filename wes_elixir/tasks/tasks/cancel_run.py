"""Celery background task to cancel workflow run and related TES tasks."""

import logging

from wes_elixir.celery_worker import celery


# Get logger instance
logger = logging.getLogger(__name__)


@celery.task(bind=True, track_started=True)
def task__cancel_run(
    self,
) -> None:
    """Revokes worfklow task and tries to cancel all running TES tasks."""
    pass
