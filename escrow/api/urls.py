from django.urls import path
from .views import EscrowListView, EscrowDetailView

app_name = 'escrow'

urlpatterns = [
    path('', EscrowListView.as_view(), name='escrow-list'),
    path('<uuid:pk>/', EscrowDetailView.as_view(), name='escrow-detail'),
]