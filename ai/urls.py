# ai/urls.py
from django.urls import path
from .views import (MaintenanceTriageView, LeaseUploadView, LeaseQueryView,
                    CopilotStreamView, EscrowStartView, EscrowResolveView)

app_name = "ai"

urlpatterns = [
    path('triage/', MaintenanceTriageView.as_view(), name='maintenance-triage'),
    path('lease/upload/', LeaseUploadView.as_view(), name='ai-lease-upload'),
    path('lease/query/', LeaseQueryView.as_view(), name='lease-query'),

    path('copilot/', CopilotStreamView.as_view(), name='copilot-stream'),

path('escrow/<int:tenancy_id>/start/', EscrowStartView.as_view(), name='escrow-start'),
    path('escrow/<int:tenancy_id>/resolve/', EscrowResolveView.as_view(), name='escrow-resolve'),
]
