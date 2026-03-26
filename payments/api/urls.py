from django.urls import path
from .views import PayRentView

app_name = 'payments'

urlpatterns = [
    path('pay-rent/', PayRentView.as_view(), name='pay-rent'),
]