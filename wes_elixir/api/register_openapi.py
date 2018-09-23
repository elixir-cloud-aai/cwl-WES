import logging
import os


# Get logger instance
logger = logging.getLogger(__name__)


def register_openapi(
    app=None,
    specs=[]
):

    '''Register OpenAPI specs with Connexion app'''

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
                swagger_json=spec['swagger_json'],
            )

            # Log info message
            logger.info("API endpoints specified in '{path}' added.".format(path=path))
        
        except (FileNotFoundError, PermissionError) as e:
            logger.critical("API specification file not found or accessible at '{path}'. Execution aborted. Original error message: {type}: {msg}".format(
                path=path,
                type=type(e).__name__,
                msg=e,
            ))
            raise SystemExit(1)

    # Return Connexion app
    return(app)