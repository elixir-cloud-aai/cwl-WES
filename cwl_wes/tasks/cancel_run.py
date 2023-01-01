"""Celery background task to cancel workflow run and related TES tasks."""

import logging
import time
from typing import List, Optional

from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app
from foca.database.register_mongodb import _create_mongo_client
from pymongo import collection as Collection
from requests import HTTPError
import tes

from cwl_wes.ga4gh.wes.states import States
import cwl_wes.utils.db as db_utils
from cwl_wes.worker import celery_app

# Get logger instance
logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.cancel_run",
    ignore_result=True,
    bind=True,
)
def task__cancel_run(
    run_id: str,
    task_id: str,
    token: Optional[str] = None,
) -> None:
    """Revokes worfklow task and tries to cancel all running TES tasks."""
    foca_config = current_app.config.foca
    # Create MongoDB client
    mongo = _create_mongo_client(
        app=current_app,
        host=foca_config.db.host,
        port=foca_config.db.port,
        db="cwl-wes-db",
    )
    collection = mongo.db["runs"]
    # Set run state to 'CANCELING'
    db_utils.set_run_state(
        collection=collection,
        run_id=run_id,
        task_id=task_id,
        state="CANCELING",
    )

    try:
        # Cancel individual TES tasks
        tes_server_config = foca_config.custom.controller.tes_server
        __cancel_tes_tasks(
            collection=collection,
            run_id=run_id,
            url=tes_server_config.url,
            timeout=tes_server_config.timeout,
            token=token,
        )
    except SoftTimeLimitExceeded as exc:
        db_utils.set_run_state(
            collection=collection,
            run_id=run_id,
            task_id=task_id,
            state="SYSTEM_ERROR",
        )
        logger.warning(
            f"Canceling workflow run '{run_id}' timed out. Run state was set "
            "to 'SYSTEM_ERROR'. Original error message: "
            f"{type(exc).__name__}: {exc}"
        )


def __cancel_tes_tasks(
    collection: Collection,
    run_id: str,
    url: str,
    timeout: int = 5,
    token: Optional[str] = None,
):
    """Cancel individual TES tasks."""
    tes_client = tes.HTTPClient(
        url=url,
        timeout=timeout,
        token=token,
    )
    canceled: List = []
    while True:
        task_ids = db_utils.find_tes_task_ids(
            collection=collection,
            run_id=run_id,
        )
        cancel = [item for item in task_ids if item not in canceled]
        for task_id in cancel:
            try:
                tes_client.cancel_task(task_id)
            except HTTPError:
                # TODO: handle more robustly: only 400/Bad Request is okay;
                # TODO: other errors (e.g. 500) should be dealt with
                pass
        canceled = canceled + cancel
        time.sleep(timeout)
        document = collection.find_one(
            filter={"run_id": run_id},
            projection={
                "api.state": True,
                "_id": False,
            },
        )
        if document["api"]["state"] in States.FINISHED:
            break
