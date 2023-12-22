"""Celery worker entry point."""

from foca.foca import Foca

foca = Foca(
    config_file="config.yaml",
    custom_config_model="cwl_wes.custom_config.CustomConfig",
)
celery_app = foca.create_celery_app()
