from connexion import App

from wes_elixir.errors.errors import handle_bad_request


def create_connexion_app(add_api=True):
    app = App(
        __name__,
        swagger_ui=True,
        swagger_json=True
    )
    if add_api:
        app.add_api(
            '../ga4gh/wes/ga4gh.wes.0_3_0.openapi.yaml',
            validate_responses=True
        )

    # Workaround for adding a custom handler for `connexion.problem` responses
    # Responses from request and paramater validators are not raised and cannot be intercepted by `add_error_handler`
    # See here: https://github.com/zalando/connexion/issues/138
    @app.app.after_request
    def rewrite_bad_request(response):
        if response.status_code == 400 and response.data.decode('utf-8').find('"title":') != None:
            response = handle_bad_request(400)
        return response

    return app
