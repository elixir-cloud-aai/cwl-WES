from connexion import App

from wes_elixir.services.config import register_config
from wes_elixir.services.cors import register_cors
from wes_elixir.services.db import register_mongodb
from wes_elixir.services.errors import handle_bad_request, register_error_handlers
from wes_elixir.services.openapi import register_openapis
from wes_elixir.services.task_queue import register_celery


def init_app():
    '''Create connexion Flask instance'''

    # Create connexion app instance
    cnx_app = App(
        __name__,
        swagger_ui=True,
        swagger_json=True,
    )

    # Register extensions
    cnx_app = register_extensions(cnx_app)

    # Return app
    return cnx_app


def register_extensions(cnx_app):
    '''Register app extensions'''

    # Register config
    cnx_app = register_config(cnx_app)

    # Register CORS
    cnx_app.app = register_cors(cnx_app.app)

    # Register error handlers
    cnx_app = register_error_handlers(cnx_app)

    # Return connexion app instance
    return cnx_app


# Instantiate connexion app
cnx_app = init_app()


# Register database
db, db_runs, db_service_info = register_mongodb(cnx_app.app)


# Register task queue
celery = register_celery(cnx_app=cnx_app)


# Workaround for adding a custom handler for `connexion.problem` responses
# Responses from request and paramater validators are not raised and cannot be intercepted by `add_error_handler`
# See here: https://github.com/zalando/connexion/issues/138
@cnx_app.app.after_request
def rewrite_bad_request(response):
    if response.status_code == 400 and response.data.decode('utf-8').find('"title":') != None:
        response = handle_bad_request(400)
    return response


def main(cnx_app):
    '''Register OpenAPI specs with connexion and start application'''

    # Register OpenAPIs
    # IMPORTANT: connexion APIs have to be registered last in order to avoid circular imports
    cnx_app = register_openapis(cnx_app)

    # Run application
    cnx_app.run()


if __name__ == '__main__':
    main(cnx_app)
