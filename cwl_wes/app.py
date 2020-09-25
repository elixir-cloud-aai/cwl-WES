"""Entry point to start service."""

from cwl_wes.api.register_openapi import register_openapi
from cwl_wes.config.app_config import parse_app_config
from foca.config.config_parser import (get_conf, get_conf_type)
from foca.config.log_config import configure_logging
from cwl_wes.database.register_mongodb import register_mongodb
from cwl_wes.errors.errors import register_error_handlers
from cwl_wes.factories.connexion_app import create_connexion_app
from cwl_wes.tasks.register_celery import register_task_service
from cwl_wes.security.cors import enable_cors


def run_server():

    # Configure logger
    configure_logging(config_var='WES_CONFIG_LOG')

    # Parse app configuration
    config = parse_app_config(config_var='WES_CONFIG')

    # Create Connexion app
    connexion_app = create_connexion_app(config)

    # Register MongoDB
    connexion_app.app = register_mongodb(connexion_app.app)

    # Register error handlers
    connexion_app = register_error_handlers(connexion_app)

    # Create Celery app and register background task monitoring service
    register_task_service(connexion_app.app)

    # Register OpenAPI specs
    connexion_app = register_openapi(
        app=connexion_app,
        specs=get_conf_type(
            config,
            'api',
            'specs',
            types=(list),
        ),
        add_security_definitions=get_conf(
            config,
            'security',
            'authorization_required'
        )
    )

    # Enable cross-origin resource sharing
    enable_cors(connexion_app.app)

    return connexion_app, config


if __name__ == '__main__':
    connexion_app, config = run_server()
    # Run app
    connexion_app.run(
        use_reloader=get_conf(config, 'server', 'use_reloader')
    )
