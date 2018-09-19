from celery import Celery


def create_celery_app(app):
    celery = Celery(
        app=__name__,
        broker='pyamqp://localhost:5672//',
        backend='rpc://',
        include=['wes_elixir.ga4gh.wes.utils_bg_tasks']
    )

    celery.conf.update(app.app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery
