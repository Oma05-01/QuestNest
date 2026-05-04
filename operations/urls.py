from django.urls import path
from .views import organisation_audit_timeline, admin_timeline

urlpatterns = [
    path("audit/", organisation_audit_timeline, name="org_audit"),
    path("timeline/", admin_timeline, name="admin-timeline"),

]