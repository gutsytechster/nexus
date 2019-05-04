# Standard Library
import os
from datetime import timedelta

# Third Party Stuff
import raven
from celery import Celery
from django.conf import settings
from dotenv import load_dotenv
from raven.contrib.celery import register_logger_signal, register_signal

# Set the default Django settings module for the 'celery' program.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')


class CeleryCustomised(Celery):

    def on_configure(self):
        client = raven.Client(os.getenv('SENTRY_DSN'), environment=os.getenv('SENTRY_ENVIRONMENT'))

        # Always ensure you import register_logger_signal, register_signal and not their parent modules
        # register a custom filter to filter out duplicate logs
        register_logger_signal(client)

        # hook into the Celery error handler
        register_signal(client)


app = CeleryCustomised('nexus')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'publish-posts': {
        'task': 'publish_posts_task',
        'schedule': timedelta(minutes=10),
    },
}
