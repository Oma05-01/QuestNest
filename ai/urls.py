# ai/urls.py
from django.urls import path
from .views import MaintenanceTriageView, LeaseUploadView, LeaseQueryView, CopilotStreamView

app_name = "ai"

urlpatterns = [
    path('triage/', MaintenanceTriageView.as_view(), name='maintenance-triage'),
    path('lease/upload/', LeaseUploadView.as_view(), name='ai-lease-upload'),
    path('lease/query/', LeaseQueryView.as_view(), name='lease-query'),

    path('copilot/', CopilotStreamView.as_view(), name='copilot-stream'),
]
