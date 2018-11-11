"""Celery background task to cancel workflow run and related TES tasks."""

import logging
from requests import HTTPError
import tes
import time
from typing import List

from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app
from pymongo import collection as Collection

from wes_elixir.celery_worker import celery
from wes_elixir.config.config_parser import get_conf
import wes_elixir.database.db_utils as db_utils
from wes_elixir.database.register_mongodb import create_mongo_client
from wes_elixir.ga4gh.wes.states import States
from wes_elixir.tasks.utils import set_run_state


# Get logger instance
logger = logging.getLogger(__name__)


@celery.task(
    name='tasks.cancel_run',
    ignore_result=True,
    bind=True,
)
def task__cancel_run(
    self,
    run_id: str,
    task_id: str,
) -> None:
    """Revokes worfklow task and tries to cancel all running TES tasks."""
    try:
        config = current_app.config
        # Create MongoDB client
        mongo = create_mongo_client(
            app=current_app,
            config=config,
        )
        collection = mongo.db['runs']
        # Set run state to 'CANCEL(ING'
        set_run_state(
            collection=collection,
            run_id=run_id,
            task_id=task_id,
            state='CANCELING',
        )
        # Cancel individual TES ta(sks
        __cancel_tes_tasks(
            collection=collection,
            run_id=run_id,
            url=get_conf(config, 'tes', 'url'),
            timeout=get_conf(config, 'tes', 'timeout'),
        )

    except SoftTimeLimitExceeded as e:
        set_run_state(
            collection=collection,
            run_id=run_id,
            task_id=task_id,
            state='SYSTEM_ERROR',
        )
        logger.warning(
            (
                "Canceling workflow run '{run_id}' timed out. Run state "
                "was set to 'SYSTEM_ERROR'. Original error message: "
                "{type}: {msg}"
            ).format(
                run_id=run_id,
                type=type(e).__name__,
                msg=e,
            )
        )


def __cancel_tes_tasks(
    collection: Collection,
    run_id: str,
    url: str,
    timeout: int = 5
):
    """Cancel individual TES tasks."""
    tes_client = tes.HTTPClient(url, timeout=timeout)
    canceled: List = list()
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
            filter={'run_id': run_id},
            projection={
                'api.state': True,
                '_id': False,
            }
        )
        if document['api']['state'] not in States.UNFINISHED:
            break
