"""cwl-WES exceptions."""

from connexion.exceptions import (
    BadRequestProblem,
    ExtraParameterProblem,
    Forbidden,
    Unauthorized,
    ProblemException,
)
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound


class WorkflowNotFound(ProblemException, NotFound):
    """WorkflowNotFound(404) error compatible with Connexion."""


exceptions = {
    Exception: {
        "message": "An unexpected error occurred.",
        "code": "500",
    },
    InternalServerError: {
        "message": "An unexpected error occurred.",
        "code": "500",
    },
    BadRequest: {
        "message": "The request is malformed.",
        "code": "400",
    },
    BadRequestProblem: {
        "message": "The request is malformed.",
        "code": "400",
    },
    ExtraParameterProblem: {
        "message": "The request is malformed.",
        "code": "400",
    },
    ValidationError: {
        "message": "The request is malformed.",
        "code": "400",
    },
    Unauthorized: {
        "message": " The request is unauthorized.",
        "code": "401",
    },
    Forbidden: {
        "message": "The requester is not authorized to perform this action.",
        "code": "403",
    },
    NotFound: {
        "message": "The requested resource wasn't found.",
        "code": "404",
    },
    WorkflowNotFound: {
        "message": "The requested workflow run wasn't found.",
        "code": "404",
    },
}
