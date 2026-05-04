from django.urls import path
from .views import (
    MaintenanceListView,
    # MaintenanceCreateView, # (If you split the Create view for file uploads, import it here)
    VendorListView,
    AssignVendorView,
    MaintenanceCommentView,
    VendorAssignmentListView,
    ApproveAndPayVendorView
)

urlpatterns = [
    # 🏠 Tenant & Landlord Core
    # GET: List all requests | POST: Create a new request
    path('', MaintenanceListView.as_view(), name='maintenance-list'),

    # 👷 Vendor Management (Organisation specific)
    # GET: List directory | POST: Add new vendor
    path('vendors/', VendorListView.as_view(), name='vendor-list'),

    # 🛠️ Landlord Management Actions
    # POST: Assign a specific vendor to a request
    path('requests/<uuid:pk>/assign/', AssignVendorView.as_view(), name='maintenance-assign'),

    # POST: Finalize task, debit organisation wallet, credit vendor wallet
    path('requests/<uuid:pk>/pay/', ApproveAndPayVendorView.as_view(), name='maintenance-pay'),

    # 💬 Communication Thread
    # GET: Fetch chat history | POST: Send a new message
    path('requests/<uuid:pk>/comments/', MaintenanceCommentView.as_view(), name='maintenance-comments'),

    # 📱 Vendor Portal
    # GET: List active jobs assigned to the currently logged-in vendor
    path('my-tasks/', VendorAssignmentListView.as_view(), name='vendor-tasks'),
]