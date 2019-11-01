"""Function to create Celery app instance and register task monitor."""

from flask import Flask
import logging
import os

from wes_elixir.factories.celery_app import create_celery_app
from wes_elixir.tasks.celery_task_monitor import TaskMonitor


# Get logger instance
logger = logging.getLogger(__name__)


def register_task_service(app: Flask) -> None:
    """Instantiates Celery app and registers task monitor."""
    # Ensure that code is executed only once when app reloader is used
    if os.environ.get("WERKZEUG_RUN_MAIN") != 'true':

        # Instantiate Celery app instance
        celery_app = create_celery_app(app)

        # Find STDOUT/STDERR endpoints
        stdout_endpoint = None
        stderr_endpoint = None
        for spec in app.config['api']['specs']:
            if spec['name'] == 'stdout_stderr':
                base_path = spec['base_path']
                stdout_endpoint = '/'.join([base_path, 'stdout'])
                stderr_endpoint = '/'.join([base_path, 'stderr'])
                break

        # Start task monitor daemon
        TaskMonitor(
            celery_app=celery_app,
            collection=app.config['database']['collections']['runs'],
            tes_config={
                'url':
                    app.config['tes']['url'],
                'logs_endpoint_root':
                    app.config['tes']['get_logs']['url_root'],
                'logs_endpoint_query_params':
                    app.config['tes']['get_logs']['query_params'],
            },
            stdout_endpoint=stdout_endpoint,
            stderr_endpoint=stderr_endpoint,
            timeout=app.config['celery']['monitor']['timeout'],
            authorization=app.config['security']['authorization_required'],
            time_format=app.config['api']['general_params']['time_format'],
        )
        logger.info('Celery task monitor registered.')

    return None
