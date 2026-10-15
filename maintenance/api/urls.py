from django.urls import path
from .views import (
    MaintenanceListView,
    VendorListView,
    AssignVendorView,
    MaintenanceCommentView,
    VendorAssignmentListView,
    ApproveAndPayVendorView
)

app_name = 'maintenance'

urlpatterns = [
    # 🟢 Maintenance Requests (Universal Endpoint)
    # GET: List requests | POST: Create request
    # Automatically routes based on Header: X-Workspace-ID
    path('', MaintenanceListView.as_view(), name='maintenance-list'),

    # 🟢 Vendor Management
    # Scoped to the active Business Workspace
    path('vendors/', VendorListView.as_view(), name='vendor-list'),

    # 🟢 Request Lifecycle & Assignments
    path('requests/<uuid:pk>/assign/', AssignVendorView.as_view(), name='maintenance-assign'),
    path('requests/<uuid:pk>/pay/', ApproveAndPayVendorView.as_view(), name='maintenance-pay'),

    # 🟢 Communication Thread
    path('requests/<uuid:pk>/comments/', MaintenanceCommentView.as_view(), name='maintenance-comments'),

    # 🟢 Vendor Portal
    # For vendors who have a personal account and tasks assigned to them
    path('my-tasks/', VendorAssignmentListView.as_view(), name='vendor-tasks'),
]