"""Entry point for Celery workers."""

from foca.factories.celery_app import create_celery_app

from cwl_wes.app import init_app

flask_app = init_app().app
celery = create_celery_app(app=flask_app)