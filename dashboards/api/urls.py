from django.urls import path
from operations.api.views import EventTraceAPIView
from .views import (TenantDashboardView, LandlordDashboardView,
                    AdminDashboardView, SystemActivityView, LandlordTenanciesView,
                    TenantPaymentHistoryView, NotificationInboxView, MarkNotificationReadView, TestWebSocketView)


app_name = 'dashboards'

urlpatterns = [
    path('tenant/', TenantDashboardView.as_view(), name='tenant-dashboard'),
    path('landlord/', LandlordDashboardView.as_view(), name='landlord-dashboard'),
    path('admin/', AdminDashboardView.as_view(), name='admin-dashboard'),

    path('landlord/tenancies/', LandlordTenanciesView.as_view(), name='landlord-tenancy-list'),

    path('tenant/payments/', TenantPaymentHistoryView.as_view(), name='tenant-payment-list'),

    path('admin/activity/', SystemActivityView.as_view(), name='system-activity'),
    path('admin/events/<uuid:pk>/trace/', EventTraceAPIView.as_view(), name='event-trace'),

    # 🟢 THE INBOX ROUTES
    path('notifications/', NotificationInboxView.as_view(), name='notification-inbox'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-read'),

    path('test-ws/', TestWebSocketView.as_view(), name='test-ws'),

]