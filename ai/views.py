# ai/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rentals.models import Tenancy
from assets.models import Unit
from maintenance.models import MaintenanceRequest
from .serializers import MaintenanceTriageRequestSerializer
from .services import triage_maintenance_issue

class MaintenanceTriageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = MaintenanceTriageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        description = serializer.validated_data['description']
        unit_id = serializer.validated_data.get('unit_id')

        # 1. Security: Enforce workspace context
        workspace = getattr(request, 'workspace', None)
        if not workspace:
            return Response(
                {"error": "Workspace context is missing. Ensure X-Workspace-ID header is set."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Resolve target unit within workspace boundaries
        unit = None
        if unit_id:
            unit = Unit.objects.filter(id=unit_id, asset__workspace=workspace).first()
            if not unit:
                return Response(
                    {"error": "Unit not found or does not belong to active workspace."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Fallback: Find resident's active tenancy unit in this workspace
            active_tenancy = Tenancy.objects.filter(
                tenant=request.user,
                workspace=workspace,
                status=Tenancy.ACTIVE
            ).select_related('unit').first()

            if active_tenancy:
                unit = active_tenancy.unit

        if not unit:
            return Response(
                {"error": "No unit linked to this request. Pass a valid `unit_id`."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 3. Execute deterministic AI triage workflow
            triage_result = triage_maintenance_issue(
                description=description,
                workspace=workspace,
                user=request.user
            )

            # 4. Map TriageResult urgency to MaintenanceRequest priority
            priority_map = {
                "low": MaintenanceRequest.LOW,
                "medium": MaintenanceRequest.MEDIUM,
                "high": MaintenanceRequest.HIGH,
                "urgent": MaintenanceRequest.URGENT,
            }
            priority = priority_map.get(triage_result.urgency.lower(), MaintenanceRequest.MEDIUM)

            # 5. Persist MaintenanceRequest record
            maintenance_request = MaintenanceRequest.objects.create(
                workspace=workspace,
                unit=unit,
                tenant=request.user,
                title=triage_result.suggested_title,
                description=f"AI Summary:\n{triage_result.summary}\n\nOriginal Resident Input:\n{description}",
                priority=priority,
                status=MaintenanceRequest.OPEN,
            )

            # 6. Build final response combining DB model metadata and AI containment guidance
            response_payload = {
                "ticket_id": str(maintenance_request.id),
                # 🟢 FIXED: Convert the datetime object to a string
                "created_at": maintenance_request.created_at.isoformat(),
                "unit": {
                    "id": str(unit.id),
                    "name": unit.name,
                },
                "triage": triage_result.model_dump(),
            }

            return Response(response_payload, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": "Failed to process triage request.", "details": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )