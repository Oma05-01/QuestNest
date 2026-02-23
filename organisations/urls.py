from django.urls import path
from .views import create_organisation, select_organisation, set_active_organisation

urlpatterns = [
    path("create/", create_organisation, name="create_organisation"),
    path("select/", select_organisation, name="select_organisation"),
    path("set/<uuid:org_id>/", set_active_organisation, name="set_active_org"),
]
