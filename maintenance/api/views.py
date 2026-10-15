from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from wallet.models import Wallet, WalletTransaction
from core.api.permissions import IsWorkspaceMember, IsBusinessWorkspace, BelongsToWorkspace
from .serializers import (
    MaintenanceSerializer, VendorSerializer,
    MaintenanceAssignmentSerializer, MaintenanceCommentSerializer
)
from ..models import MaintenanceRequest, MaintenanceImage, MaintenanceAssignment, Vendor


class MaintenanceListView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        # 🟢 Filter based on the active workspace context
        if request.workspace.workspace_type == 'business':
            # Managers see all requests for their workspace
            requests = MaintenanceRequest.objects.filter(workspace=request.workspace)
        else:
            # Tenants see requests they personally submitted
            requests = MaintenanceRequest.objects.filter(tenant=request.user)

        return Response(MaintenanceSerializer(requests, many=True).data)

    def post(self, request):
        serializer = MaintenanceSerializer(data=request.data)
        if serializer.is_valid():
            # 🟢 INFERENCE: Get the unit to find out which business workspace owns it
            unit = serializer.validated_data.get('unit')

            maintenance_request = serializer.save(
                tenant=request.user,
                workspace=unit.workspace,  # Auto-routed to the correct manager!
            )

            # Handle image uploads
            images = request.FILES.getlist('images')
            for image in images:
                MaintenanceImage.objects.create(request=maintenance_request, image=image)

            return Response(MaintenanceSerializer(maintenance_request).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorListView(generics.ListCreateAPIView):
    """ GET/POST /api/maintenance/vendors/ """
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, IsBusinessWorkspace]

    def get_queryset(self):
        # Vendors are scoped to the business workspace
        return Vendor.objects.filter(workspace=self.request.workspace)

    def perform_create(self, serializer):
        serializer.save(workspace=self.request.workspace)


class AssignVendorView(APIView):
    """ POST /api/maintenance/requests/<pk>/assign/ """
    permission_classes = [IsAuthenticated, IsBusinessWorkspace, BelongsToWorkspace]

    def post(self, request, pk):
        # BelongsToWorkspace ensures the manager owns this request
        m_request = get_object_or_404(MaintenanceRequest, pk=pk, workspace=request.workspace)
        vendor_id = request.data.get('vendor_id')

        assignment = MaintenanceAssignment.objects.create(
            request=m_request,
            vendor_id=vendor_id,
            notes=request.data.get('notes', '')
        )

        m_request.status = MaintenanceRequest.IN_PROGRESS
        m_request.save()

        return Response(MaintenanceAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class ApproveAndPayVendorView(APIView):
    """ POST /api/maintenance/requests/<pk>/pay/ """
    permission_classes = [IsAuthenticated, IsBusinessWorkspace, BelongsToWorkspace]

    def post(self, request, pk):
        with transaction.atomic():
            # 1. Lock the request for update
            m_request = get_object_or_404(
                MaintenanceRequest.objects.select_for_update(),
                pk=pk,
                workspace=request.workspace
            )

            assignment = m_request.assignments.last()
            if not assignment:
                return Response({"error": "No vendor assigned."}, status=status.HTTP_400_BAD_REQUEST)

            cost = request.data.get('cost')
            if not cost or float(cost) <= 0:
                return Response({"error": "Valid cost required."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Debit the Business Workspace Wallet
            # 🟢 CHANGED: Pointing to workspace instead of organisation
            workspace_wallet = Wallet.objects.select_for_update().get(workspace=request.workspace)

            if workspace_wallet.balance < float(cost):
                return Response({"error": "Insufficient workspace funds."}, status=status.HTTP_400_BAD_REQUEST)

            WalletTransaction.objects.create(
                wallet=workspace_wallet,
                amount=cost,
                transaction_type='debit',
                description=f"Maintenance Payout: {m_request.title}",
                reference=f"MNT-{m_request.id.hex[:6]}"
            )

            # 3. Credit the Vendor's Personal Wallet
            # (Assuming vendor email links to a User record)
            vendor_user = assignment.vendor.linked_user  # Recommended addition to Vendor model
            vendor_wallet, _ = Wallet.objects.get_or_create(user=vendor_user)

            WalletTransaction.objects.create(
                wallet=vendor_wallet,
                amount=cost,
                transaction_type='credit',
                description=f"Work Order Payment: {m_request.title}"
            )

            # 4. Finalize
            assignment.cost = cost
            assignment.save()
            m_request.status = MaintenanceRequest.CLOSED
            m_request.save()

            return Response({"message": "Vendor paid and request closed."})


class MaintenanceCommentView(APIView):
    """ GET /api/maintenance/requests/<pk>/comments/ & POST """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get(self, request, pk):
        # 🟢 Security: Ensure the user has access to the request's context
        if request.workspace.workspace_type == 'business':
            m_request = get_object_or_404(MaintenanceRequest, pk=pk, workspace=request.workspace)
        else:
            m_request = get_object_or_404(MaintenanceRequest, pk=pk, tenant=request.user)

        comments = m_request.comments.all().order_by('created_at')
        serializer = MaintenanceCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, pk):
        # 🟢 Authorization: Must be part of the request context to comment
        if request.workspace.workspace_type == 'business':
            m_request = get_object_or_404(MaintenanceRequest, pk=pk, workspace=request.workspace)
        else:
            m_request = get_object_or_404(MaintenanceRequest, pk=pk, tenant=request.user)

        serializer = MaintenanceCommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Automatically set the author and the request
            serializer.save(author=request.user, request=m_request)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorAssignmentListView(APIView):
    """ GET /api/maintenance/my-tasks/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns jobs assigned to the current user's email.
        Note: We don't use 'request.workspace' here because the vendor
        is acting as an external service provider.
        """
        assignments = MaintenanceAssignment.objects.filter(
            vendor__email=request.user.email
        ).select_related(
            'request',
            'request__unit',
            'request__unit__asset'
        ).order_by('-assigned_at')

        serializer = MaintenanceAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)