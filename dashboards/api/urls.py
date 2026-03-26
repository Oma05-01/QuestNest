from django.urls import path
from .views import TenantDashboardView, LandlordDashboardView, AdminDashboardView

app_name = 'dashboards'

urlpatterns = [
    path('tenant/', TenantDashboardView.as_view(), name='tenant-dashboard'),
    path('landlord/', LandlordDashboardView.as_view(), name='landlord-dashboard'),
    path('admin/', AdminDashboardView.as_view(), name='admin-dashboard'),
]