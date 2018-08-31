import flask
import json


def handle_bad_request(exception):
    return flask.Response(
        response=json.dumps({
            'msg': 'The request is malformed.',
            'status_code': '400'
            }),
        status=400,
        mimetype="application/json"
    )

def handle_unauthorized(exception):
    return flask.Response(
        response=json.dumps({
            'msg': 'The request is unauthorized.',
            'status_code': '401'
            }),
        status=401,
        mimetype="application/json"
    )

def handle_forbidden(exception):
    return flask.Response(
        response=json.dumps({
            'msg': 'The requester is not authorized to perform this action.',
            'status_code': '403'
            }),
        status=403,
        mimetype="application/json"
    )

def handle_workflow_not_found(exception):
    return flask.Response(
        response=json.dumps({
            'msg': 'The requested workflow run wasn\'t found.',
            'status_code': '404'
            }),
        status=404,
        mimetype="application/json"
    )

def handle_internal_server_error(exception):
    return flask.Response(
        response=json.dumps({
            'msg': 'An unexpected error occurred.',
            'status_code': '500'
            }),
        status=500,
        mimetype="application/json"
    )