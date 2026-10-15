from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

# 🟢 New Permissions
from core.api.permissions import IsWorkspaceMember, IsBusinessWorkspace
from rentals.models import Tenancy
from .serializers import TenancySerializer, CreateTenancySerializer


class TenancyListCreateView(generics.ListCreateAPIView):
    """
    GET /api/tenancies/
    POST /api/tenancies/ (Business Workspace only)
    """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateTenancySerializer
        return TenancySerializer

    def get_permissions(self):
        # 🟢 Only Property Managers (Business) can create new leases
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsBusinessWorkspace()]
        return super().get_permissions()

    @extend_schema(summary="List Tenancies", responses=TenancySerializer(many=True))
    def get_queryset(self):
        # 🟢 Context Split: Return data based on the active workspace type!

        # 1. If acting as a Property Manager...
        if self.request.workspace.workspace_type == 'business':
            return Tenancy.objects.filter(
                workspace=self.request.workspace
            ).select_related('unit', 'unit__asset', 'tenant').order_by('-start_date')

        # 2. If acting as a Tenant...
        else:
            return Tenancy.objects.filter(
                tenant=self.request.user
            ).select_related('unit', 'unit__asset').order_by('-start_date')

    @extend_schema(summary="Create a Tenancy (Lease)", request=CreateTenancySerializer,
                   responses={201: TenancySerializer})
    def perform_create(self, serializer):
        # The serializer's validate_unit method already checked if the unit belongs to this workspace!
        # The model's save() method automatically attaches the workspace!
        serializer.save()


class TenancyDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/tenancies/<pk>/
    PATCH /api/tenancies/<pk>/ (Business Workspace only)
    """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    serializer_class = TenancySerializer

    def get_permissions(self):
        # Only Property Managers (Business) can edit a lease
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsBusinessWorkspace()]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.workspace.workspace_type == 'business':
            return Tenancy.objects.filter(workspace=self.request.workspace)
        else:
            return Tenancy.objects.filter(tenant=self.request.user)