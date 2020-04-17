"""Entry point for Celery workers."""

from cwl_wes.config.app_config import parse_app_config
from cwl_wes.factories.celery_app import create_celery_app
from cwl_wes.factories.connexion_app import create_connexion_app


# Parse app configuration
config = parse_app_config(config_var='WES_CONFIG')

# Create Celery app
celery = create_celery_app(create_connexion_app(config).app)
