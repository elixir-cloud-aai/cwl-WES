import os

from connexion import App

from wes_elixir.errors.errors import handle_bad_request
from wes_elixir.factories.celery_app import create_celery_app


def create_connexion_app(add_api=True, monitoring=True):

    # Instantiate connexion app
    app = App(
        __name__,
        swagger_ui=True,
        swagger_json=True
    )

    # Generate API endpoints from OpenAPI specs (only for main app!)
    if add_api:
        app.add_api(
            '../ga4gh/wes/ga4gh.wes.0_3_0.openapi.yaml',
            validate_responses=True
    )

    # Start celery task monitoring daemon (only for main app!)
    # Second condition ensures block is executed only once when 'use_reloader' is True
    if monitoring and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        celery = create_celery_app(app)
        from wes_elixir.monitoring.celery_tasks import TaskMonitor
        TaskMonitor(celery)

    # Workaround for adding a custom handler for `connexion.problem` responses
    # Responses from request and paramater validators are not raised and cannot be intercepted by `add_error_handler`
    # See here: https://github.com/zalando/connexion/issues/138
    @app.app.after_request
    def rewrite_bad_request(response):
        if response.status_code == 400 and response.data.decode('utf-8').find('"title":') != None:
            response = handle_bad_request(400)
        return response

    # Return connexion app
    return app
