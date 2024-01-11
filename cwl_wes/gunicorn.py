"""Gunicorn entry point."""

import os

from cwl_wes.app import init_app

# Source application configuration
app = init_app().app
app_config = app.config.foca

# Set Gunicorn number of workers and threads
workers = int(os.environ.get("GUNICORN_PROCESSES", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "1"))

# Set allowed IPs
forwarded_allow_ips = "*"  # pylint: disable=invalid-name

# Set Gunicorn bind address
bind = f"{app_config.server.host}:{app_config.server.port}"

# Source the environment variables for the Gunicorn workers
raw_env = [
    f"WES_CONFIG={os.environ.get('WES_CONFIG', '')}",
    f"RABBIT_HOST={os.environ.get('RABBIT_HOST', app_config.jobs.host)}",
    f"RABBIT_PORT={os.environ.get('RABBIT_PORT', app_config.jobs.port)}",
    f"MONGO_HOST={os.environ.get('MONGO_HOST', app_config.db.host)}",
    f"MONGO_PORT={os.environ.get('MONGO_PORT', app_config.db.port)}",
    f"MONGO_DBNAME={os.environ.get('MONGO_DBNAME', 'cwl-wes-db')}",
    f"MONGO_USERNAME={os.environ.get('MONGO_USERNAME', '')}",
    f"MONGO_PASSWORD={os.environ.get('MONGO_PASSWORD', '')}",
]
