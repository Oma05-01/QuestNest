from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from workspaces.models import Workspace
from assets.models import Assets
# 🟢 UPDATED: Using our new context-aware permissions
from core.api.permissions import IsBusinessWorkspace, BelongsToWorkspace
from verification.services.verification_service import (
    submit_workspace_verification,
    submit_asset_verification
)
from .serializers import SubmitVerificationSerializer


class SubmitVerificationView(APIView):
    """
    POST /api/verification/submit/
    Only Business Workspaces can submit verification documents.
    """
    permission_classes = [IsAuthenticated, IsBusinessWorkspace]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = SubmitVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_type = serializer.validated_data['target_type']
        target_id = serializer.validated_data['target_id']
        documents = serializer.validated_data['documents']

        # 🟢 CASE 1: Verifying the Business Entity itself
        if target_type == 'workspace':
            # Ensure the target workspace is the one the user is currently acting in
            workspace = get_object_or_404(Workspace, id=target_id)

            if workspace != request.workspace:
                return Response(
                    {"error": "You can only verify your active business workspace."},
                    status=status.HTTP_403_FORBIDDEN
                )

            submit_workspace_verification(
                workspace=workspace,
                document_file=documents[0],
                submitter=request.user
            )
            return Response({"message": "Workspace identity documents submitted for review."})

        # 🟢 CASE 2: Verifying a Specific Building/Asset
        elif target_type == 'asset':
            # Ensure the asset belongs to the active workspace context
            asset = get_object_or_404(Assets, id=target_id, workspace=request.workspace)

            submit_asset_verification(
                asset=asset,
                document_files=documents,
                submitter=request.user
            )
            return Response({"message": "Property ownership documents submitted for review."})

        return Response({"error": "Invalid target type."}, status=status.HTTP_400_BAD_REQUEST)