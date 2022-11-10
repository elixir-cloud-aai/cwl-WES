"""Function to create Celery app instance and register task monitor."""

from connexion import App
import logging
import os

from foca.factories.celery_app import create_celery_app
from pymongo.collection import Collection

from cwl_wes.tasks.celery_task_monitor import TaskMonitor


# Get logger instance
logger = logging.getLogger(__name__)


def register_task_service(app: App) -> None:
    """Instantiates Celery app and registers task monitor."""
    # Ensure that code is executed only once when app reloader is used
    if os.environ.get("WERKZEUG_RUN_MAIN") != 'true':
        # Start task monitor daemon
        foca_config = app.app.config.foca
        custom_config = foca_config.custom
        celery_app = create_celery_app(app.app)
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
