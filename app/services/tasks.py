from celery import Celery


def make_celery(app, result_backend, broker_url):
    '''Instantiate Celery object and overwrite Task class'''

    # Instantiate Celery object with backend and broker paths
    celery = Celery(
        app.import_name,
        backend=result_backend,
        broker=broker_url
    )

    # Update Celery config from Flask app config
    celery.conf.update(app.config)

    # Overwrite __call__ function of `celery.Task` class to avoid explicitly adding `app.context()` every time a task is run
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    # Return Celery instance
    return celery