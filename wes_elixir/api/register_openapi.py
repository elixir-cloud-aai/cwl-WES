import logging
import os
from shutil import copyfile

from wes_elixir.config.config_parser import get_conf


# Get logger instance
logger = logging.getLogger(__name__)


def register_openapi(
    app=None,
    specs=[],
    add_security_definitions=True
):

    """Registers OpenAPI specs with Connexion app."""

    # Iterate over list of API specs
    for spec in specs:

        # Get _this_ directory
        path = os.path.join(
            os.path.abspath(
                os.path.dirname(
                    os.path.realpath(__file__)
                )
            ),
            get_conf(spec, 'path')
        )

        # Add security definitions to copy of specs
        if add_security_definitions:
            path = __add_security_definitions(in_file=path)

        # Generate API endpoints from OpenAPI spec
        try:
            app.add_api(
                path,
                strict_validation=get_conf(spec, 'strict_validation'),
                validate_responses=get_conf(spec, 'validate_responses'),
                swagger_ui=get_conf(spec, 'swagger_ui'),
                swagger_json=get_conf(spec, 'swagger_json'),
            )

            # Log info message
            logger.info("API endpoints specified in '{path}' added.".format(
                path=path,
            ))

        except (FileNotFoundError, PermissionError) as e:
            logger.critical(
                (
                    "API specification file not found or accessible at "
                    "'{path}'. Execution aborted. Original error message: "
                    "{type}: {msg}"
                ).format(
                    path=path,
                    type=type(e).__name__,
                    msg=e,
                )
            )
            raise SystemExit(1)

    # Return Connexion app
    return(app)


def __add_security_definitions(
    in_file,
    ext='modified.yaml'
):

    """Adds 'securityDefinitions' section to OpenAPI YAML specs."""

    # Set security definitions
    amend = '''

# Amended by WES-ELIXIR
securityDefinitions:
  jwt:
    type: apiKey
    name: Authorization
    in: header'''

    # Create copy for modification
    out_file = '.'.join([os.path.splitext(in_file)[0], ext])
    copyfile(in_file, out_file)

    # Append security definitions
    with open(out_file, 'a') as mod:
        mod.write(amend)

    # Return modified file path
    return out_file
