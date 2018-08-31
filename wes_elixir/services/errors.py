from connexion import ProblemException
from connexion.exceptions import ExtraParameterProblem, Forbidden, Unauthorized
from flask import Response
from json import dumps
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound


def register_error_handlers(cnx_app):
    '''Add custom handlers for exceptions to connexion app instance'''

    # Add error handlers
    cnx_app.add_error_handler(BadRequest, handle_bad_request)
    cnx_app.add_error_handler(ExtraParameterProblem, handle_bad_request)
    cnx_app.add_error_handler(Forbidden, __handle_forbidden)
    cnx_app.add_error_handler(InternalServerError, __handle_internal_server_error)
    cnx_app.add_error_handler(Unauthorized, __handle_unauthorized)
    cnx_app.add_error_handler(WorkflowNotFound, __handle_workflow_not_found)

    # Return connexion app instance
    return cnx_app


# CUSTOM ERRORS
class WorkflowNotFound(ProblemException, NotFound):
    '''WorkflowNotFound(404) error compatible with connexion'''
    def __init__(self, title=None, **kwargs):
        super(WorkflowNotFound, self).__init__(title=title, **kwargs)


# CUSTOM ERROR HANDLERS
def handle_bad_request(exception):
    return Response(
        response=dumps({
            'msg': 'The request is malformed.',
            'status_code': '400'
            }),
        status=400,
        mimetype="application/problem+json"
    )

def __handle_unauthorized(exception):
    return Response(
        response=dumps({
            'msg': 'The request is unauthorized.',
            'status_code': '401'
            }),
        status=401,
        mimetype="application/problem+json"
    )

def __handle_forbidden(exception):
    return Response(
        response=dumps({
            'msg': 'The requester is not authorized to perform this action.',
            'status_code': '403'
            }),
        status=403,
        mimetype="application/problem+json"
    )

def __handle_workflow_not_found(exception):
    return Response(
        response=dumps({
            'msg': 'The requested workflow run wasn\'t found.',
            'status_code': '404'
            }),
        status=404,
        mimetype="application/problem+json"
    )

def __handle_internal_server_error(exception):
    return Response(
        response=dumps({
            'msg': 'An unexpected error occurred.',
            'status_code': '500'
            }),
        status=500,
        mimetype="application/problem+json"
    )