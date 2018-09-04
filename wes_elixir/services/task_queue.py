from celery import Celery


def register_celery(cnx_app):
    '''Instantiate Celery object from connexion app object; adds `app.context()` to Task'''

    # Instantiate Celery object with backend and broker paths
    celery = Celery(
        cnx_app.import_name,
        backend=cnx_app.app.config['celery']['result_backend'],
        broker=cnx_app.app.config['celery']['broker_url']
    )

    # Update Celery config from Flask app config
    celery.conf.update(cnx_app.app.config)

    # Overwrite __call__ function of `celery.Task` class
    # `app.context()` does not need to be added explicitly when running a task
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with cnx_app.app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    # Return Celery instance
    return celery
