from django.urls import path
from . import views

urlpatterns = [
    path('tenant/', views.tenant_dashboard, name='tenant_dashboard'),
    path('landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('agent/', views.agent_dashboard, name='agent_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]
