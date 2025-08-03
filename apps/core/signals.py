from django.db.models.signals import post_migrate
from django.dispatch import receiver
import os
import logging

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def handle_post_migrate(sender, **kwargs):
    """
    Signal handler that logs when migrations are complete
    """
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        logger.info("Migrations have been applied successfully on Railway deployment")
