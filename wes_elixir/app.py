"""Entry point to start service."""

from wes_elixir.api.register_openapi import register_openapi
from wes_elixir.config.app_config import parse_app_config
from wes_elixir.config.config_parser import (get_conf, get_conf_type)
from wes_elixir.config.log_config import configure_logging
from wes_elixir.database.register_mongodb import register_mongodb
from wes_elixir.errors.errors import register_error_handlers
from wes_elixir.factories.connexion_app import create_connexion_app
from wes_elixir.tasks.register_celery import register_task_service
from wes_elixir.security.cors import enable_cors


def main():

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
        specs=get_conf_type(config, 'api', 'specs', types=(list)),
        add_security_definitions=get_conf(
            config,
            'security',
            'authorization_required'
        )
    )

    # Enable cross-origin resource sharing
    enable_cors(connexion_app.app)

    # Run app
    connexion_app.run(
        use_reloader=get_conf(config, 'server', 'use_reloader')
    )


if __name__ == '__main__':
    main()
