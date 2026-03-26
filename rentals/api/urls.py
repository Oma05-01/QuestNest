from django.urls import path
from .views import MyTenanciesView

app_name = 'rentals'

urlpatterns = [
    path('me/', MyTenanciesView.as_view(), name='my-tenancies'),
]