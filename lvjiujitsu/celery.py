import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvjiujitsu.settings")

app = Celery("lvjiujitsu")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
