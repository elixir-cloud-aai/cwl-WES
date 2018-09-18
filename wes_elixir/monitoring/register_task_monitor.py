import os

from wes_elixir.factories.celery_app import create_celery_app
from wes_elixir.monitoring.celery_task_monitor import TaskMonitor


def register_task_monitor(connexion_app):
    '''Instantiate celery app and register task monitor'''

    # Ensure that code is executed only once when app reloader is used (in debug mode)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":

        # Instantiate Celery app instance
        celery_app = create_celery_app(connexion_app)

        # Start task monitor daemon
        TaskMonitor(celery_app, connexion_app)

    # Nothing to return
    return None
