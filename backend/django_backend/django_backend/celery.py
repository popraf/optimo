import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.settings')

celery_app = Celery('django_backend')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
celery_app.autodiscover_tasks()

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    'check-reservation-deadlines-every-day': {
        'task': 'app.tasks.check_reservation_deadlines',
        'schedule': 86400,  # once every 24 hours
    },
}
