from wes_elixir.factories.celery_app import create_celery_app
from wes_elixir.factories.connexion_app import create_connexion_app


celery = create_celery_app(create_connexion_app(add_api=False, monitoring=False))
