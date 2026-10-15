from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from drf_spectacular.utils import extend_schema

from workspaces.models import Workspace, Membership
from .serializers import WorkspaceSerializer, CreateWorkspaceSerializer


class MyWorkspacesView(APIView):
    """
    GET: List all workspaces the human belongs to (Personal & Business).
    POST: Create a new Business Workspace (Property Management Company).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List My Workspaces",
        description="Returns all workspaces where the user is an active member.",
        responses=WorkspaceSerializer(many=True)
    )
    def get(self, request):
        # 🟢 Find every workspace where this human is an active member
        workspaces = Workspace.objects.filter(
            members__user=request.user,
            members__is_active=True
        ).distinct()

        # Pass request in context so the serializer can calculate 'my_role'
        serializer = WorkspaceSerializer(workspaces, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Create Business Workspace",
        request=CreateWorkspaceSerializer,
        responses={201: WorkspaceSerializer}
    )
    def post(self, request):
        serializer = CreateWorkspaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # 1. Create the Workspace as a BUSINESS type
            workspace = Workspace.objects.create(
                name=serializer.validated_data['name'],
                workspace_type=Workspace.BUSINESS
            )

            # 2. Immediately make the creator the OWNER of this new business
            Membership.objects.create(
                user=request.user,
                workspace=workspace,
                role=Membership.OWNER
            )

            # 🟢 REMOVED: request.user.organisation = organisation
            # We no longer store the "active" workspace on the User record.
            # The frontend will now just start sending 'X-Workspace-ID' for this new ID.

        return Response(
            WorkspaceSerializer(workspace, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )