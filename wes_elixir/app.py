from flask_cors import CORS

from wes_elixir.api.register_openapi import register_openapi
from wes_elixir.config.app_config import parse_app_config
from wes_elixir.config.log_config import configure_logging
from wes_elixir.database.register_mongodb import register_mongodb
from wes_elixir.errors.errors import register_error_handlers
from wes_elixir.factories.connexion_app import create_connexion_app
from wes_elixir.monitoring.register_task_monitor import register_task_monitor


def main():

    # Configure logger
    configure_logging(config_var='WES_CONFIG_LOG')

    # Parse app configuration
    config = parse_app_config(config_var='WES_CONFIG')

    # Create connexion app
    connexion_app = create_connexion_app(config)

    # Register MongoDB
    connexion_app = register_mongodb(connexion_app)

    # Register error handlers
    connexion_app = register_error_handlers(connexion_app)

    # Register OpenAPI specs with connexion app
    connexion_app = register_openapi(
        app=connexion_app,
        specs=config['api']['specs']
    )

    # Register celery background task monitoring service
    register_task_monitor(connexion_app)

    # Enable cross-origin resource sharing
    CORS(connexion_app.app)

    # Run app
    connexion_app.run(
        use_reloader=config['server']['use_reloader']
    )


if __name__ == '__main__':
    main()