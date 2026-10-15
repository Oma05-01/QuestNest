from django.urls import path
from .views import TenancyListCreateView, TenancyDetailView

app_name = 'rentals'

urlpatterns = [
    # Replaces 'me/'. Handles listing for both Tenants and Managers!
    path('', TenancyListCreateView.as_view(), name='tenancy-list-create'),

    # Detail view for a specific lease
    path('<int:pk>/', TenancyDetailView.as_view(), name='tenancy-detail'),
]