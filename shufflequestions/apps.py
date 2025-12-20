from django.apps import AppConfig
from django.conf import settings


class ShufflequestionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shufflequestions'

    def ready(self):
        print("Cleaner started...")
        # if not settings.DEBUG:
        # print("🟢 Starting scheduler from external file...")
        from .utils.clean_up_scheduler import start_scheduler
        start_scheduler()  # ✅ no 'self.'
