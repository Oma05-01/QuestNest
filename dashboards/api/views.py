from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
import logging
from operations.models import Event
from rentals.models import Tenancy
from payments.models import Payment
from notifications.models import Notification
from notifications.api.serializers import NotificationSerializer

# 🟢 Updated Permissions
from core.api.permissions import (
    IsPersonalWorkspace, IsBusinessWorkspace,
    IsSystemAdmin, BelongsToWorkspace, IsWorkspaceMember
)

# 🟢 Updated Serializers (using the ones we just refactored)
from .serializers import (
    EventListSerializer,
    WorkspaceTenancyListSerializer,
    PaymentHistorySerializer
)

# Services (These will also need a workspace update internally)
from dashboards.services.dashboard_service import (
    get_tenant_dashboard_data,
    get_landlord_dashboard_data,
    get_admin_dashboard_data
)

from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers

logger = logging.getLogger(__name__)

class TenantDashboardView(APIView):
    """ GET /api/dashboard/stats/personal/ -> Personal Workspace Stats """
    permission_classes = [IsAuthenticated, IsPersonalWorkspace]

    def get(self, request):
        workspace = getattr(request, 'workspace', None)
        workspace_id = workspace.id if workspace else 'default'
        cache_key = f"personal_stats_{workspace_id}_{request.user.id}"

        data = cache.get(cache_key)
        if not data:
            try:
                data = get_tenant_dashboard_data(request.user, workspace=workspace)
                cache.set(cache_key, data, 300)
            except Exception as e:
                logger.error(f"Error in TenantDashboardView: {e}", exc_info=True)
                # Fallback structure preventing HTTP 500
                data = {
                    "total_paid": 0,
                    "next_rent_due": None,
                    "active_leases": 0
                }

        return Response(data)


class LandlordDashboardView(APIView):
    """ GET /api/dashboard/stats/business/ -> Business Workspace Stats """
    permission_classes = [IsAuthenticated, IsBusinessWorkspace]

    def get(self, request):
        workspace = getattr(request, 'workspace', None)
        workspace_id = workspace.id if workspace else 'default'
        cache_key = f"business_stats_{workspace_id}_{request.user.id}"

        data = cache.get(cache_key)
        if not data:
            try:
                data = get_landlord_dashboard_data(request.user, workspace=workspace)
                cache.set(cache_key, data, 300)
            except Exception as e:
                logger.error(f"Error in LandlordDashboardView: {e}", exc_info=True)
                data = {
                    "total_revenue": 0,
                    "escrow_balance": 0,
                    "active_tenants": 0
                }

        return Response(data)


class AdminDashboardView(APIView):
    """ GET /api/dashboard/stats/admin/ -> System-wide Stats """
    permission_classes = [IsAuthenticated, IsSystemAdmin]

    def get(self, request):
        cache_key = "admin_system_stats"
        data = cache.get(cache_key)

        if not data:
            data = get_admin_dashboard_data(request.user)
            cache.set(cache_key, data, 300)

        return Response(data)
# --- List Views ---

class SystemActivityView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsSystemAdmin]
    serializer_class = EventListSerializer

    def get_queryset(self):
        # System admins see everything across all workspaces
        return Event.objects.select_related('workspace', 'actor').order_by('-created_at')

class LandlordTenanciesView(generics.ListAPIView):
    """ List tenancies for the active Business Workspace """
    permission_classes = [IsAuthenticated, IsBusinessWorkspace, BelongsToWorkspace]
    serializer_class = WorkspaceTenancyListSerializer

    def get_queryset(self):
        # 🟢 Filter strictly by the workspace attached by middleware
        return Tenancy.objects.select_related('tenant', 'unit').filter(
            workspace=self.request.workspace
        ).order_by('next_payment_date')

class TenantPaymentHistoryView(generics.ListAPIView):
    """ List payments for the active Personal Workspace """
    permission_classes = [IsAuthenticated, IsPersonalWorkspace, BelongsToWorkspace]
    serializer_class = PaymentHistorySerializer

    def get_queryset(self):
        # 🟢 Filter by the personal workspace context
        return Payment.objects.select_related('tenancy', 'tenancy__unit').filter(
            workspace=self.request.workspace
        ).order_by('-created_at')

class NotificationInboxView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get_queryset(self):
        # 🟢 Get notifications for this human user WITHIN this workspace
        return Notification.objects.filter(
            user=self.request.user,
            workspace=self.request.workspace
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unread_count = queryset.filter(is_read=False).count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['unread_count'] = unread_count
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "unread_count": unread_count,
            "results": serializer.data
        })

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def patch(self, request, pk):
        # 🟢 Security: Ensure notification belongs to user AND current workspace
        notification = generics.get_object_or_404(
            Notification,
            pk=pk,
            user=request.user,
            workspace=request.workspace
        )
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"status": "marked as read"}, status=status.HTTP_200_OK)