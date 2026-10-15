from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers, generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer

# 🟢 NEW: Clean, context-aware permissions
from core.api.permissions import IsBusinessWorkspace, BelongsToWorkspace, IsWorkspaceMember
from leases.models import LeaseAgreement, LeaseSignature
from leases.services.lease_service import (
    create_lease_from_tenancy,
    send_lease_for_signature,
    sign_lease
)
from .serializers import LeaseSerializer, CreateLeaseSerializer


class LeaseListView(APIView):
    """ GET /api/leases/ & POST /api/leases/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(summary="List Leases", responses=LeaseSerializer(many=True))
    def get(self, request):
        # 🟢 Filter based on the active workspace type
        if request.workspace.workspace_type == 'business':
            # Managers see leases belonging to this business workspace
            leases = LeaseAgreement.objects.filter(tenancy__workspace=request.workspace)
        else:
            # Tenants (Personal WS) see leases where they are the individual tenant
            leases = LeaseAgreement.objects.filter(tenancy__tenant=request.user)

        leases = leases.prefetch_related('clauses', 'signatures').order_by('-created_at')
        return Response(LeaseSerializer(leases, many=True).data)

    @extend_schema(summary="Generate Lease", request=CreateLeaseSerializer, responses={201: LeaseSerializer})
    def post(self, request):
        # 🟢 Strict Permission: Only Business Workspaces can generate leases
        if request.workspace.workspace_type != 'business':
            return Response({"detail": "Only business workspaces can generate leases."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateLeaseSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        lease = create_lease_from_tenancy(
            tenancy=serializer.validated_data['tenancy_id'],
            actor=request.user
        )
        return Response(LeaseSerializer(lease).data, status=status.HTTP_201_CREATED)


class LeaseSendView(APIView):
    """ POST /api/leases/<uuid:pk>/send/ """
    permission_classes = [IsAuthenticated, IsBusinessWorkspace, BelongsToWorkspace]

    @extend_schema(summary="Send Lease for Signature",
                   responses={200: inline_serializer(name='SendLeaseRes', fields={'message': serializers.CharField()})})
    def post(self, request, pk):
        # 🟢 Security: BelongsToWorkspace handles the ownership check!
        lease = get_object_or_404(LeaseAgreement, pk=pk)

        if lease.status != LeaseAgreement.DRAFT:
            return Response({"error": "Only draft leases can be sent."}, status=status.HTTP_400_BAD_REQUEST)

        send_lease_for_signature(lease=lease, actor=request.user)
        return Response({"message": "Lease sent for signature successfully."}, status=status.HTTP_200_OK)


class LeaseSignView(APIView):
    """ POST /api/leases/<uuid:pk>/sign/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    @extend_schema(summary="Sign Lease",
                   responses={200: inline_serializer(name='SignLeaseRes', fields={'message': serializers.CharField()})})
    def post(self, request, pk):
        lease = get_object_or_404(LeaseAgreement, pk=pk)

        # 🟢 Security: Check involvement via active context
        is_tenant = lease.tenancy.tenant == request.user
        is_landlord = (request.workspace.workspace_type == 'business' and
                       lease.tenancy.workspace == request.workspace)

        if not (is_tenant or is_landlord):
            return Response({"error": "You do not have permission to sign this lease."},
                            status=status.HTTP_403_FORBIDDEN)

        if lease.status not in [LeaseAgreement.SENT, LeaseAgreement.SIGNED]:
            return Response({"error": "Lease is not pending signature."}, status=status.HTTP_400_BAD_REQUEST)

        role = LeaseSignature.TENANT if is_tenant else LeaseSignature.LANDLORD

        if lease.signatures.filter(user=request.user).exists():
            return Response({"error": "You have already signed this lease."}, status=status.HTTP_400_BAD_REQUEST)

        sign_lease(
            lease=lease,
            user=request.user,
            role=role,
            request=request
        )

        return Response({"message": "Lease signed successfully."}, status=status.HTTP_200_OK)


class LeaseDetailView(generics.RetrieveAPIView):
    """ GET /api/leases/<uuid:pk>/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    serializer_class = LeaseSerializer

    @extend_schema(summary="Get Lease Details")
    def get_queryset(self):
        # 🟢 Context-aware filtering
        if self.request.workspace.workspace_type == 'business':
            return LeaseAgreement.objects.filter(tenancy__workspace=self.request.workspace)
        return LeaseAgreement.objects.filter(tenancy__tenant=self.request.user)