"""Function enabling cross-origin resource sharing for a Connexion app
instance."""

import logging

from flask_cors import CORS


# Get logger instance
logger = logging.getLogger(__name__)


def enable_cors(app):
    """Enables cross-origin resource sharing for Connexion app."""

    # Enable CORS
    CORS(app)
    logger.info('Enabled CORS for Connexion app.')
