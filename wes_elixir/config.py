import os

from wes_elixir.config.config_parser import get_conf
from wes_elixir.config.app_config import parse_app_config

flask_config = parse_app_config(config_var='WES_CONFIG')

workers = int(os.environ.get('GUNICORN_PROCESSES', '3'))
threads = int(os.environ.get('GUNICORN_THREADS', '1'))

forwarded_allow_ips = '*'

# Source the environment variables for the Gunicorn workers
raw_env = [
    "RABBIT_HOST=%s" % os.environ.get('RABBIT_HOST', get_conf(flask_config, 'celery', 'broker_host')),
    "RABBIT_PORT=%s" % os.environ.get('RABBIT_PORT', get_conf(flask_config, 'celery', 'broker_port')),
    "MONGO_HOST=%s" % os.environ.get('MONGO_HOST', get_conf(flask_config, 'database', 'host')),
    "MONGO_PORT=%s" % os.environ.get('MONGO_PORT', get_conf(flask_config, 'database', 'port')),
    "MONGO_DBNAME=%s" % os.environ.get('MONGO_DBNAME', get_conf(flask_config, 'database', 'name')),
    "MONGO_USERNAME=%s" % os.environ.get('MONGO_USERNAME', None),
    "MONGO_PASSWORD=%s" % os.environ.get('MONGO_PASSWORD', None)
]
