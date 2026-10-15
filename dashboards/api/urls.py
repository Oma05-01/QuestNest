from django.urls import path
from operations.api.views import EventTraceAPIView
from .views import (
    TenantDashboardView,
    LandlordDashboardView,
    AdminDashboardView,
    SystemActivityView,
    LandlordTenanciesView,
    TenantPaymentHistoryView,
    NotificationInboxView,
    MarkNotificationReadView,
)

app_name = 'dashboards'

urlpatterns = [
    # --- Dashboard Stats (Aggregated Data) ---
    # Gated by IsPersonalWorkspace
    path('stats/personal/', TenantDashboardView.as_view(), name='personal-stats'),

    # Gated by IsBusinessWorkspace
    path('stats/business/', LandlordDashboardView.as_view(), name='business-stats'),

    # Gated by IsSystemAdmin
    path('stats/admin/', AdminDashboardView.as_view(), name='admin-stats'),

    # --- Resource Lists (Context-Aware) ---
    # These automatically filter by the Workspace in the Header
    path('tenancies/', LandlordTenanciesView.as_view(), name='tenancy-list'),
    path('payments/', TenantPaymentHistoryView.as_view(), name='payment-history'),

    # --- System Administration ---
    path('admin/activity/', SystemActivityView.as_view(), name='system-activity'),
    path('admin/events/<uuid:pk>/trace/', EventTraceAPIView.as_view(), name='event-trace'),

    # --- Notifications & Live Updates ---
    path('notifications/', NotificationInboxView.as_view(), name='notification-inbox'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-read'),

]