from django.apps import AppConfig
import sys

class RecordingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recordings'
    def ready(self):
        if 'runserver' not in sys.argv and 'uwsgi' not in sys.argv and 'gunicorn' not in sys.argv:
            return
        import recordings.signals
