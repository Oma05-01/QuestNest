from django.urls import path
from .views import LeaseListView, LeaseDetailView, LeaseSendView, LeaseSignView

app_name = 'leases'

urlpatterns = [
    path('', LeaseListView.as_view(), name='lease-list-create'),
    path('<uuid:pk>/', LeaseDetailView.as_view(), name='lease-detail'),
    path('<uuid:pk>/send/', LeaseSendView.as_view(), name='lease-send'),
    path('<uuid:pk>/sign/', LeaseSignView.as_view(), name='lease-sign'),
]