from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from escrow.services.escrow_service import EscrowService

from escrow.models import Escrow
from .serializers import EscrowSerializer
from core.api.permissions import IsWorkspaceMember, BelongsToWorkspace

class EscrowListView(APIView):
    """ GET /api/escrows/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(summary="List Escrows", responses=EscrowSerializer(many=True))
    def get(self, request):
        # 🟢 Filter strictly based on active Workspace Type
        if request.workspace.workspace_type == 'business':
            # Landlords/Managers see all escrows tied to their Business Workspace
            escrows = Escrow.objects.filter(workspace=request.workspace)
        else:
            # Tenants (Personal) only see escrows where they are the individual tenant
            escrows = Escrow.objects.filter(tenant=request.user)

        # 🟢 Optimized hit using the direct workspace relationship
        escrows = escrows.select_related(
            'tenant',
            'workspace',
            'tenancy__unit'
        ).order_by('-created_at')

        serializer = EscrowSerializer(escrows, many=True)
        return Response(serializer.data)


class EscrowDetailView(APIView):
    """ GET /api/escrows/<uuid:pk>/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember, BelongsToWorkspace]

    @extend_schema(summary="Get Escrow Details", responses=EscrowSerializer)
    def get(self, request, pk):
        # 🟢 Security: Ensure the escrow belongs to either this business OR this personal user
        if request.workspace.workspace_type == 'business':
            escrow = get_object_or_404(Escrow, pk=pk, workspace=request.workspace)
        else:
            escrow = get_object_or_404(Escrow, pk=pk, tenant=request.user)

        serializer = EscrowSerializer(escrow)
        return Response(serializer.data)


class EscrowFundView(APIView):
    """ POST /api/escrows/<uuid:pk>/fund/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def post(self, request, pk):
        try:
            # Usually, only the tenant funds an escrow.
            # The Service Layer should verify if the actor has sufficient balance.
            escrow = EscrowService.fund_escrow_from_wallet(
                escrow_id=pk,
                actor=request.user
            )
            return Response({
                "message": "Escrow funded successfully",
                "status": escrow.status
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "An unexpected error occurred during funding."}, status=500)