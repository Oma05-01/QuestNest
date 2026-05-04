from django.utils import timezone
from django.core.cache import cache  # 🟢 Added for Phase 11
from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status

from operations.models import Event
from rentals.models import Tenancy
from payments.models import Payment
from notifications.models import Notification
from notifications.api.serializers import NotificationSerializer
from .serializers import EventListSerializer, LandlordTenancyListSerializer, TenantPaymentHistorySerializer
from core.api.permissions import IsTenant, IsLandlord, IsAdmin, BelongsToOrganisation

# Import the heavy-lifting service functions
from dashboards.services.dashboard_service import (
    get_tenant_dashboard_data,
    get_landlord_dashboard_data,
    get_admin_dashboard_data
)

from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

class TenantDashboardView(APIView):
    """
    GET /api/dashboard/tenant/
    """
    permission_classes = [IsAuthenticated, IsTenant]

    @extend_schema(
        summary="Tenant Dashboard Stats",
        responses={
            200: inline_serializer(
                name='TenantDashboardResponse',
                fields={
                    'total_paid': serializers.DecimalField(max_digits=10, decimal_places=2),
                    'next_rent_due': serializers.DateField(),
                    'active_leases': serializers.IntegerField(),
                }
            )
        }
    )
    def get(self, request):
        cache_key = f"tenant_stats_{request.user.id}"
        data = cache.get(cache_key)

        if not data:
            # Cache miss: Run the service logic
            data = get_tenant_dashboard_data(request.user)
            # Store in Redis for 10 minutes
            cache.set(cache_key, data, 600)

        return Response(data)

class LandlordDashboardView(APIView):
    """
    GET /api/dashboard/landlord/
    """
    permission_classes = [IsAuthenticated, IsLandlord, BelongsToOrganisation]

    @extend_schema(
        summary="Landlord Dashboard Stats",
        responses={
            200: inline_serializer(
                name='LandlordDashboardResponse',
                fields={
                    'total_revenue': serializers.DecimalField(max_digits=12, decimal_places=2),
                    'active_tenants': serializers.IntegerField(),
                    'escrow_balance': serializers.DecimalField(max_digits=12, decimal_places=2),
                }
            )
        }
    )
    def get(self, request):
        org_id = request.user.organisation.id
        cache_key = f"landlord_stats_{org_id}"
        data = cache.get(cache_key)

        if not data:
            data = get_landlord_dashboard_data(request.user)
            cache.set(cache_key, data, 600)

        return Response(data)

class AdminDashboardView(APIView):
    """
    GET /api/dashboard/admin/
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        summary="Admin System Stats",
        responses={
            200: inline_serializer(
                name='AdminDashboardResponse',
                fields={
                    'total_users': serializers.IntegerField(),
                    'active_escrows': serializers.IntegerField(),
                    'system_health': serializers.CharField(),
                }
            )
        }
    )
    def get(self, request):
        cache_key = "admin_system_stats"
        data = cache.get(cache_key)

        if not data:
            data = get_admin_dashboard_data(request.user)
            cache.set(cache_key, data, 300)

        return Response(data)

# --- List Views (Already optimized via select_related in get_queryset) ---

class SystemActivityView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = EventListSerializer

    @extend_schema(
        summary="List System Activity",
        description="Retrieve all system events. Filterable by status and event type.",
        parameters=[
            OpenApiParameter(name='status', description='Filter by status (e.g., failed, success)', required=False,
                             type=str),
            OpenApiParameter(name='event_type', description='Filter by event type (e.g., PAYMENT_SUCCESS)',
                             required=False, type=str),
            OpenApiParameter(name='organisation_id', description='Filter by Org ID', required=False,
                             type=OpenApiTypes.UUID),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Event.objects.select_related('organisation', 'actor').order_by('-created_at')
        # ... (filtering logic remains same)


class LandlordTenanciesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsLandlord, BelongsToOrganisation]
    serializer_class = LandlordTenancyListSerializer

    def get_queryset(self):
        org = self.request.user.organisation
        return Tenancy.objects.select_related('tenant', 'unit').filter(organisation=org).order_by('next_payment_date')
        # ... (filtering logic remains same)


class TenantPaymentHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTenant, BelongsToOrganisation]
    serializer_class = TenantPaymentHistorySerializer

    def get_queryset(self):
        return Payment.objects.select_related('tenancy', 'tenancy__unit').filter(user=self.request.user).order_by(
            '-created_at')


class NotificationInboxView(generics.ListAPIView):
    """
    GET /api/dashboard/notifications/
    Returns notifications and the unread count.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Calculate unread count efficiently
        unread_count = queryset.filter(is_read=False).count()

        # Paginate or serialize the list as usual
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['unread_count'] = unread_count  # Inject the badge count
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "unread_count": unread_count,  # Inject the badge count
            "results": serializer.data
        })


class MarkNotificationReadView(APIView):
    @extend_schema(
        summary="Mark Notification as Read",
        responses={200: inline_serializer(name='MarkReadResponse', fields={'status': serializers.CharField()})}
    )
    def patch(self, request, pk):
        notification = generics.get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"status": "marked as read"}, status=status.HTTP_200_OK)


# Add this at the bottom of your dashboards views
class TestWebSocketView(APIView):
    """ Temporary view to test live WebSockets """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]  # Ensures we know who is testing

    def get(self, request):
        from notifications.services.notification_service import trigger_notification

        # Manually trigger a smart notification for the logged-in user
        trigger_notification(
            user=request.user,
            title="System Alert",
            message="Your WebSocket is fully operational!",
            notification_type="success",
            send_email=False,
            metadata={
                "action": {
                    "type": "OPEN_MODAL",
                    "target": "PAYMENT_RECEIPT",
                    "params": {"reference": "TEST-12345"}
                }
            }
        )
        return Response({"status": "WebSocket payload fired!"})