# celery.py
import os
from celery import Celery

# TODO: Change 'your_main_project_folder' to the actual name of the folder this file is in
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questnest.settings')

app = Celery('questnest')

# This tells Celery to read the settings we just added in settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# This tells Celery to automatically look for a 'tasks.py' file in all your apps
app.autodiscover_tasks()