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
            timeout=app.app.config['celery']['monitor']['timeout'],
            authorization=app.app.config['security']['authorization_required'],
            tes={
                'url': app.app.config['tes']['url'],
                'logs_endpoint_root': app.app.config['tes']['get_logs']['url_root'],
                'logs_endpoint_query_params': app.app.config['tes']['get_logs']['query_params'],
            },
        )
        logger.info("Celery task monitor registered.")

    # Nothing to return
    return None