from django.urls import path
from .views import EscrowListView, EscrowDetailView, EscrowFundView

app_name = 'escrow'

urlpatterns = [
    path('', EscrowListView.as_view(), name='escrow-list'),
    path('<uuid:pk>/', EscrowDetailView.as_view(), name='escrow-detail'),
    path('<uuid:pk>/fund/', EscrowFundView.as_view(), name='escrow-fund'),
]