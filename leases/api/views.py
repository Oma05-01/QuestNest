from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from core.api.permissions import IsLandlordOrAdmin, IsTenant
from leases.models import LeaseAgreement, LeaseSignature
from leases.services.lease_service import (
    create_lease_from_tenancy,
    send_lease_for_signature,
    sign_lease
)
from .serializers import LeaseSerializer, CreateLeaseSerializer


class LeaseListView(APIView):
    """ GET /api/leases/ & POST /api/leases/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        leases = LeaseAgreement.objects.filter(
            Q(tenancy__tenant=request.user) | Q(tenancy__unit__asset__owner=request.user)
        ).prefetch_related('clauses', 'signatures')

        return Response(LeaseSerializer(leases, many=True).data)

    def post(self, request):
        # Only Landlords/Admins should generate leases
        if request.user.role not in ['landlord', 'admin']:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateLeaseSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        lease = create_lease_from_tenancy(
            tenancy=serializer.validated_data['tenancy_id'],
            actor=request.user
        )
        return Response(LeaseSerializer(lease).data, status=status.HTTP_201_CREATED)


class LeaseSendView(APIView):
    """ POST /api/leases/<uuid:pk>/send/ """
    permission_classes = [IsAuthenticated, IsLandlordOrAdmin]

    def post(self, request, pk):
        lease = get_object_or_404(LeaseAgreement, pk=pk, tenancy__unit__asset__owner=request.user)

        if lease.status != LeaseAgreement.DRAFT:
            return Response({"error": "Only draft leases can be sent."}, status=400)

        send_lease_for_signature(lease=lease, actor=request.user)
        return Response({"message": "Lease sent for signature successfully."})


class LeaseSignView(APIView):
    """ POST /api/leases/<uuid:pk>/sign/ """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        lease = get_object_or_404(LeaseAgreement, pk=pk)

        # Verify lease is ready to be signed
        if lease.status not in [LeaseAgreement.SENT, LeaseAgreement.SIGNED]:
            return Response({"error": "Lease is not pending signature."}, status=400)

        # Determine role based on who is making the request
        role = LeaseSignature.TENANT if request.user.role == 'tenant' else LeaseSignature.LANDLORD

        # Prevent double signing
        if lease.signatures.filter(user=request.user).exists():
            return Response({"error": "You have already signed this lease."}, status=400)

        # No serializer needed! Your service grabs everything it needs from the User and Request objects.
        sign_lease(
            lease=lease,
            user=request.user,
            role=role,
            request=request  # Passes the request down to extract the IP address
        )

        return Response({"message": "Lease signed successfully."}, status=status.HTTP_200_OK)