from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
from escrow.models import Escrow
from .serializers import EscrowSerializer


class EscrowListView(APIView):
    """ GET /api/escrows/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # A user only sees escrows where they are either the tenant OR the landlord
        escrows = Escrow.objects.filter(
            Q(tenant=request.user) | Q(landlord=request.user)
        ).select_related('tenant', 'landlord', 'tenancy__unit').order_by('-created_at')

        serializer = EscrowSerializer(escrows, many=True)
        return Response(serializer.data)


class EscrowDetailView(APIView):
    """ GET /api/escrows/<uuid:pk>/ """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # get_object_or_404 ensures a 404 response instead of a 500 crash if not found
        escrow = get_object_or_404(
            Escrow.objects.select_related('tenant', 'landlord', 'tenancy__unit'),
            pk=pk,
            # Security: ensure they own this specific escrow
            tenant=request.user
        ) if request.user.role == 'tenant' else get_object_or_404(
            Escrow.objects.select_related('tenant', 'landlord', 'tenancy__unit'),
            pk=pk,
            landlord=request.user
        )

        serializer = EscrowSerializer(escrow)
        return Response(serializer.data)