"""Entry point for Celery workers."""

from wes_elixir.config.app_config import parse_app_config
from wes_elixir.factories.celery_app import create_celery_app
from wes_elixir.factories.connexion_app import create_connexion_app


# Parse app configuration
config = parse_app_config(config_var='WES_CONFIG')

# Create Celery app
celery = create_celery_app(create_connexion_app(config).app)
