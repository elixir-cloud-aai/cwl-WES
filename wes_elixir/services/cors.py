from flask_cors import CORS


def register_cors(app):
    '''Apply cross-origin resource sharing to Flask app instance'''
    CORS(app)
    return(app)