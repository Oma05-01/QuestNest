from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Import the custom permissions we just built
from core.api.permissions import IsTenant, IsLandlord, IsAdmin

# Import the heavy-lifting service functions
from dashboards.services.dashboard_service import (
    get_tenant_dashboard_data,
    get_landlord_dashboard_data,
    get_admin_dashboard_data
)

class TenantDashboardView(APIView):
    """
    GET /api/dashboard/tenant/
    """
    permission_classes = [IsAuthenticated, IsTenant]

    def get(self, request):
        data = get_tenant_dashboard_data(request.user)
        return Response(data)


class LandlordDashboardView(APIView):
    """
    GET /api/dashboard/landlord/
    """
    permission_classes = [IsAuthenticated, IsLandlord]

    def get(self, request):
        data = get_landlord_dashboard_data(request.user)
        return Response(data)


class AdminDashboardView(APIView):
    """
    GET /api/dashboard/admin/
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        data = get_admin_dashboard_data(request.user)
        return Response(data)