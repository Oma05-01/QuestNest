from django.urls import path
from .views import LeaseListView, LeaseSendView, LeaseSignView

app_name = 'leases'

urlpatterns = [
    path('', LeaseListView.as_view(), name='lease-list'),
    path('<uuid:pk>/send/', LeaseSendView.as_view(), name='lease-send'),
    path('<uuid:pk>/sign/', LeaseSignView.as_view(), name='lease-sign'),
]