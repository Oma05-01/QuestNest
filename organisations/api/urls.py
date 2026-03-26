from django.urls import path
from .views import MyOrganisationsView

app_name = 'organisations'

urlpatterns = [
    path('', MyOrganisationsView.as_view(), name='organisation-list'),
]