from django.urls import path
from .views import organisation_audit_timeline

urlpatterns = [
path("audit/", organisation_audit_timeline, name="org_audit")
]
