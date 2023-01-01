"""cwl-WES application entry point."""

from pathlib import Path

from connexion import App
from flask import current_app
from foca import Foca

from cwl_wes.ga4gh.wes.service_info import ServiceInfo
from cwl_wes.exceptions import NotFound


def init_app() -> App:
    """Initialize FOCA application.

    Returns:
        App: FOCA application.
    """
    foca = Foca(
        config_file=Path("config.yaml"),
        custom_config_model="cwl_wes.custom_config.CustomConfig",
    )
    app = foca.create_app()
    with app.app.app_context():
        service_info = ServiceInfo()
        try:
            service_info.get_service_info()
        except NotFound:
            service_info.set_service_info(
                data=current_app.config.foca.custom.service_info.dict()
            )
    return app


def run_app(app: App) -> None:
    """Run FOCA application."""
    app.run(port=app.port)


if __name__ == "__main__":
    my_app = init_app()
    run_app(my_app)
