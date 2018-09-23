import logging
import os


def register_openapi(app, specs, validate_responses=True):
    '''Register OpenAPI specs with connexion app'''

    # Iterate over list of APIspecs
    for spec in specs:

        # Extract path
        path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), spec['path']))

        # Generate API endpoints from OpenAPI specs
        try:
            app.add_api(
                path, 
                strict_validation=spec['strict_validation'],
                validate_responses=spec['validate_responses'],
                swagger_ui=spec['swagger_ui'],
                swagger_json=spec['swagger_json']
            )

            # Log info message
            logging.info("API endpoints specified in '{path}' added.".format(path=path))
        
        except FileNotFoundError as e:
            logging.error("{e}".format(e=e))

    # Return connexion app
    return(app)