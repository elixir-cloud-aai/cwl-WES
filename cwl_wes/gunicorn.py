import os

from cwl_wes.app import init_app

# Source application configuration
app = init_app().app
app_config = app.config.foca

# Set Gunicorn number of workers and threads
workers = int(os.environ.get("GUNICORN_PROCESSES", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "1"))

# Set allowed IPs
forwarded_allow_ips = "*"

# Set Gunicorn bind address
bind = "{address}:{port}".format(
    address=app_config.server.host,
    port=app_config.server.port,
)

# Source the environment variables for the Gunicorn workers
raw_env = [
    "WES_CONFIG=%s" % os.environ.get("WES_CONFIG", ""),
    "RABBIT_HOST=%s" % os.environ.get("RABBIT_HOST", app_config.jobs.host),
    "RABBIT_PORT=%s" % os.environ.get("RABBIT_PORT", app_config.jobs.port),
    "MONGO_HOST=%s" % os.environ.get("MONGO_HOST", app_config.db.host),
    "MONGO_PORT=%s" % os.environ.get("MONGO_PORT", app_config.db.port),
    "MONGO_DBNAME=%s" % os.environ.get("MONGO_DBNAME", "cwl-wes-db"),
    "MONGO_USERNAME=%s" % os.environ.get("MONGO_USERNAME", ""),
    "MONGO_PASSWORD=%s" % os.environ.get("MONGO_PASSWORD", ""),
]
