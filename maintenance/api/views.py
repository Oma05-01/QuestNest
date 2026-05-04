# maintenance/api/views.py
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from wallet.models import Wallet, WalletTransaction
from .serializers import MaintenanceSerializer, VendorSerializer, MaintenanceAssignmentSerializer, \
    MaintenanceCommentSerializer
from ..models import MaintenanceRequest, MaintenanceImage, MaintenanceAssignment, Vendor
from rest_framework.parsers import MultiPartParser, FormParser

class MaintenanceListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        if request.user.role == 'tenant':
            requests = MaintenanceRequest.objects.filter(tenant=request.user)
        else:
            requests = MaintenanceRequest.objects.filter(organisation=request.user.organisation)

        # Serialize and return (omitting serializer code for brevity)
        return Response(MaintenanceSerializer(requests, many=True).data)

    def post(self, request):
        serializer = MaintenanceSerializer(data=request.data)

        if serializer.is_valid():
            # 1. Save the main request
            maintenance_request = serializer.save(
                tenant=request.user,
                organisation=request.user.organisation if request.user.role != 'tenant' else request.data.get(
                    'unit_org'),
                unit_id=request.data.get('unit')
            )

            # 2. Handle multiple images
            images = request.FILES.getlist('images')
            for image in images:
                MaintenanceImage.objects.create(request=maintenance_request, image=image)

            return Response(MaintenanceSerializer(maintenance_request).data, status=201)

        return Response(serializer.errors, status=400)


class VendorListView(generics.ListCreateAPIView):
    """ GET /api/maintenance/vendors/ & POST """
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Multi-tenant security
        return Vendor.objects.filter(organisation=self.request.user.organisation)

    def perform_create(self, serializer):
        serializer.save(organisation=self.request.user.organisation)


class AssignVendorView(APIView):
    """ POST /api/maintenance/requests/<pk>/assign/ """

    def post(self, request, pk):
        m_request = get_object_or_404(MaintenanceRequest, pk=pk, organisation=request.user.organisation)
        vendor_id = request.data.get('vendor_id')

        assignment = MaintenanceAssignment.objects.create(
            request=m_request,
            vendor_id=vendor_id,
            notes=request.data.get('notes', '')
        )

        # Automatically bump the request status to "In Progress"
        m_request.status = MaintenanceRequest.IN_PROGRESS
        m_request.save()

        return Response(MaintenanceAssignmentSerializer(assignment).data, status=201)


class MaintenanceCommentView(APIView):
    """ GET /api/maintenance/requests/<pk>/comments/ & POST """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        m_request = get_object_or_404(MaintenanceRequest, pk=pk)
        # Ensure the user has access to this request's org
        if request.user.role != 'tenant' and m_request.organisation != request.user.organisation:
            return Response(status=403)

        comments = m_request.comments.all()
        return Response(MaintenanceCommentSerializer(comments, many=True, context={'request': request}).data)

    def post(self, request, pk):
        m_request = get_object_or_404(MaintenanceRequest, pk=pk)
        serializer = MaintenanceCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, request=m_request)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class VendorAssignmentListView(APIView):
    """ GET /api/maintenance/my-tasks/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # We assume the Vendor is a User in the system with a specific role
        # or linked to a Vendor object.
        assignments = MaintenanceAssignment.objects.filter(
            vendor__email=request.user.email
        ).select_related('request', 'request__unit')

        # We'll need a quick serializer for this
        serializer = MaintenanceAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


User = get_user_model()


class ApproveAndPayVendorView(APIView):
    """ POST /api/maintenance/requests/<pk>/pay/ """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # 1. Fetch the request and ensure it belongs to the Landlord's Organisation
        m_request = get_object_or_404(
            MaintenanceRequest.objects.select_for_update(),
            pk=pk,
            organisation=request.user.organisation
        )

        # 2. Get the active assignment
        assignment = m_request.assignments.last()
        if not assignment:
            return Response({"error": "No vendor assigned to this request."}, status=400)

        if m_request.status == MaintenanceRequest.CLOSED:
            return Response({"error": "This request has already been closed and paid."}, status=400)

        # 3. Get the final cost from the frontend
        final_cost = request.data.get('cost')
        if not final_cost or float(final_cost) <= 0:
            return Response({"error": "A valid payout amount is required."}, status=400)

        final_cost = float(final_cost)

        try:
            with transaction.atomic():
                # --- A. DEBIT THE LANDLORD (ORGANISATION) ---
                org_wallet = Wallet.objects.select_for_update().get(organisation=m_request.organisation)

                if org_wallet.balance < final_cost:
                    return Response({
                        "error": f"Insufficient funds. Wallet Balance: ₦{org_wallet.balance}, Required: ₦{final_cost}"
                    }, status=400)

                WalletTransaction.objects.create(
                    wallet=org_wallet,
                    amount=final_cost,
                    transaction_type=WalletTransaction.DEBIT,
                    description=f"Maintenance Payout: {m_request.title} ({assignment.vendor.name})",
                    reference=f"MNT-PAY-{m_request.id.hex[:8]}"
                )

                # --- B. CREDIT THE VENDOR ---
                # Find the Vendor's user account via the email on their Vendor profile
                vendor_user = User.objects.filter(email=assignment.vendor.email).first()
                if not vendor_user:
                    raise Exception("Vendor does not have a registered system account to receive funds.")

                vendor_wallet, _ = Wallet.objects.get_or_create(user=vendor_user, defaults={'organisation': None})

                WalletTransaction.objects.create(
                    wallet=vendor_wallet,
                    amount=final_cost,
                    transaction_type=WalletTransaction.CREDIT,
                    description=f"Payment for Work Order: {m_request.title}",
                    reference=f"MNT-REC-{m_request.id.hex[:8]}"
                )

                # --- C. UPDATE MAINTENANCE RECORDS ---
                assignment.cost = final_cost
                assignment.completed_at = transaction.now()
                assignment.save()

                m_request.status = MaintenanceRequest.CLOSED
                m_request.save()

            return Response({"message": "Vendor paid successfully and request closed."}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=400)


