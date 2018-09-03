def register_openapis(cnx_app):
    '''Add OpenAPI specification to connexion app instance'''

    # Register GA4GH WES API (https://github.com/ga4gh/workflow-execution-service-schemas)
    cnx_app.add_api(
        cnx_app.app.config['openapi']['wes_yaml_specs'],
        # TODO: put this to config
        base_path="/ga4gh/wes/v1",
        strict_validation=True,
        validate_responses=True,
    )

    # Return connexion app instance
    return(cnx_app)