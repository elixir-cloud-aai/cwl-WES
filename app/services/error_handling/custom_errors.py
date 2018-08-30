import connexion
import werkzeug.exceptions


class BadRequest(connexion.ProblemException, werkzeug.exceptions.BadRequest):
    '''BadRequest(400) error compatible with connexion'''
    def __init__(self, title=None, **kwargs):
        super(BadRequest, self).__init__(title=title, **kwargs)

class WorkflowNotFound(connexion.ProblemException, werkzeug.exceptions.NotFound):
    '''WorkflowNotFound(404) error compatible with connexion'''
    def __init__(self, title=None, **kwargs):
        super(WorkflowNotFound, self).__init__(title=title, **kwargs)

class InternalServerError(connexion.ProblemException, werkzeug.exceptions.InternalServerError):
    '''InternalServerError(500) error compatible with connexion'''
    def __init__(self, title=None, **kwargs):
        super(InternalServerError, self).__init__(title=title, **kwargs)