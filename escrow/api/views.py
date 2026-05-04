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


class EscrowListView(APIView):
    """ GET /api/escrows/ """
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="List Escrows", responses=EscrowSerializer(many=True))
    def get(self, request):
        # 🟢 FIX: Clean separation of Tenant vs Organisation queries
        if request.user.role == 'tenant':
            escrows = Escrow.objects.filter(tenant=request.user)
        else:
            # Landlords and Agents see all escrows tied to their Organisation
            escrows = Escrow.objects.filter(tenancy__unit__asset__organisation=request.user.organisation)

        # Optimize the database hit
        escrows = escrows.select_related(
            'tenant',
            'tenancy__unit',
            'tenancy__unit__asset__organisation'
        ).order_by('-created_at')

        serializer = EscrowSerializer(escrows, many=True)
        return Response(serializer.data)


class EscrowDetailView(APIView):
    """ GET /api/escrows/<uuid:pk>/ """
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Get Escrow Details", responses=EscrowSerializer)
    def get(self, request, pk):
        # 🟢 FIX: Ensure proper security scopes using Organisation
        if request.user.role == 'tenant':
            escrow = get_object_or_404(
                Escrow.objects.select_related('tenant', 'tenancy__unit', 'tenancy__unit__asset__organisation'),
                pk=pk,
                tenant=request.user
            )
        else:
            escrow = get_object_or_404(
                Escrow.objects.select_related('tenant', 'tenancy__unit', 'tenancy__unit__asset__organisation'),
                pk=pk,
                tenancy__unit__asset__organisation=request.user.organisation
            )

        serializer = EscrowSerializer(escrow)
        return Response(serializer.data)


class EscrowFundView(APIView):
    """ POST /api/escrows/<uuid:pk>/fund/ """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            # We call our service to handle the heavy lifting
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
        except Exception as e:
            return Response({"error": "An unexpected error occurred."}, status=500)