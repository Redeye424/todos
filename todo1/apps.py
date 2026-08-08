from django.apps import AppConfig
import os


class Todo1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'todo1'

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        from .scheduler import start_scheduler
        start_scheduler()