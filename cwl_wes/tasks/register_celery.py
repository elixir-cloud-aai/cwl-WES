"""Function to create Celery app instance and register task monitor."""

from celery import Celery
import logging
import os

from cwl_wes.tasks.celery_task_monitor import TaskMonitor


# Get logger instance
logger = logging.getLogger(__name__)


def register_task_service(celery_app: Celery) -> None:
    """Instantiates Celery app and registers task monitor."""
    # Ensure that code is executed only once when app reloader is used
    if os.environ.get("WERKZEUG_RUN_MAIN") != 'true':
        # Start task monitor daemon
        foca_config = celery_app.conf.foca
        custom_config = foca_config.custom
        TaskMonitor(
            celery_app=celery_app,
            collection=foca_config.db.dbs['cwl-wes-db'].collections['runs'].client,
            tes_config={
                'url': custom_config.tes_server.url,
                'query_params': custom_config.tes_server.status_query_params,
                'timeout': custom_config.tes_server.timeout
            },
            timeout=custom_config.celery.monitor.timeout,
            authorization=foca_config.security.auth.required,
        )
        logger.info('Celery task monitor registered.')

    return None
