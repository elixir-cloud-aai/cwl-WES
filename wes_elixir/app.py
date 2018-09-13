from flask_cors import CORS

from wes_elixir.config.config import config_connexion_app
from wes_elixir.database.register_mongodb import register_mongodb
from wes_elixir.errors.errors import register_error_handlers
from wes_elixir.factories.connexion_app import create_connexion_app


def main():
    connexion_app = create_connexion_app()
    connexion_app = config_connexion_app(connexion_app)
    connexion_app = register_mongodb(connexion_app)
    connexion_app = register_error_handlers(connexion_app)
    CORS(connexion_app.app)
    connexion_app.run()


if __name__ == '__main__':
    main()