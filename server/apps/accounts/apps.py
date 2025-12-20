from django.apps import AppConfig
import sys

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        # Prevent initialization during migrations or management commands that don't need it
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            from .broadcaster import broadcaster
            broadcaster.initialize(bind_port=6666, target_port=6667)
