import logging
import os

from wes_elixir.factories.celery_app import create_celery_app
from wes_elixir.tasks.celery_task_monitor import TaskMonitor


# Get logger instance
logger = logging.getLogger(__name__)


def register_task_service(app):
    '''Instantiate Celery app and register task monitor'''

    # Ensure that code is executed only once when app reloader is used (in debug mode)
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":

        # Instantiate Celery app instance
        celery_app = create_celery_app(app)

        # Start task monitor daemon
        TaskMonitor(
            celery_app=celery_app,
            collection=app.app.config['database']['collections']['runs'],
            timeout=app.app.config['celery']['monitor']['timeout']
        )
        logger.info("Celery task monitor registered.")

    # Nothing to return
    return None