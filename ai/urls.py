# ai/urls.py
from django.urls import path
from .views import MaintenanceTriageView

app_name = "ai"

urlpatterns = [
    path('triage/', MaintenanceTriageView.as_view(), name='maintenance-triage'),
]