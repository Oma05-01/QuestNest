from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404

# 🟢 NEW: Imported our shiny new Context Security permissions!
from core.api.permissions import IsWorkspaceMember, IsBusinessWorkspace, BelongsToWorkspace

from assets.models import Assets, Unit
from .serializers import AssetSerializer, CreateAssetSerializer, UnitSerializer, CreateUnitSerializer
from operations.services.event_service import log_event
from operations.constants import EventType


class AssetListCreateView(APIView):
    """ GET /api/assets/ & POST /api/assets/ """

    def get_permissions(self):
        # 🟢 CHANGED: Landlords (Business Workspaces) create, anyone with a workspace can read
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsBusinessWorkspace(), BelongsToWorkspace()]
        return [IsAuthenticated(), IsWorkspaceMember()]

    @extend_schema(summary="List Assets", responses=AssetSerializer(many=True))
    def get(self, request):
        # 🟢 CHANGED: Filter strictly by the active workspace!
        if request.workspace.workspace_type == 'business':
            assets = Assets.objects.filter(workspace=request.workspace)
        else:
            # Tenants (Personal Workspaces) only see public/listed properties
            assets = Assets.objects.filter(status=Assets.LISTED)

        search_query = request.GET.get("q", "")
        if search_query:
            assets = assets.filter(name__icontains=search_query) | assets.filter(location__icontains=search_query)

        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Create Asset", request=CreateAssetSerializer, responses={201: AssetSerializer})
    def post(self, request):
        serializer = CreateAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 🟢 CHANGED: The beauty of DRF ModelSerializers!
        # We auto-inject the workspace from the middleware. Unhackable.
        asset = serializer.save(workspace=request.workspace)

        # Log the creation event
        log_event(
            workspace=request.workspace,
            actor=request.user,
            event_type=EventType.PROPERTY_CREATED,  # Assuming you have this!
            object_type="Asset",
            object_id=str(asset.id)
        )

        return Response(AssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ GET, PATCH, DELETE /api/assets/<pk>/ """

    # 🟢 CHANGED: Strict Business Workspace permissions
    permission_classes = [IsAuthenticated, IsBusinessWorkspace, BelongsToWorkspace]
    serializer_class = AssetSerializer

    def get_queryset(self):
        # 🟢 CHANGED: Ensure landlords can only touch properties in their workspace
        return Assets.objects.filter(workspace=self.request.workspace)

    @extend_schema(summary="Update Asset")
    def perform_update(self, serializer):
        asset = self.get_object()

        old_values = {field: getattr(asset, field) for field in serializer.validated_data.keys()}
        updated_asset = serializer.save()

        changed_fields = {}
        for field, old_val in old_values.items():
            new_val = getattr(updated_asset, field)
            if old_val != new_val:
                changed_fields[field] = {"old": old_val, "new": new_val}

        if changed_fields:
            log_event(
                workspace=updated_asset.workspace,  # 🟢 CHANGED
                actor=self.request.user,
                event_type=EventType.PROPERTY_UPDATED,
                object_type="Asset",
                object_id=str(updated_asset.id),
                metadata={"changed_fields": changed_fields}
            )

    @extend_schema(summary="Delete Asset")
    def perform_destroy(self, instance):
        workspace = instance.workspace
        asset_id = str(instance.id)

        instance.delete()

        # Log the deletion
        log_event(
            workspace=workspace,
            actor=self.request.user,
            event_type=EventType.PROPERTY_DELETED,  # Assuming you have this!
            object_type="Asset",
            object_id=asset_id
        )


class UnitListCreateView(APIView):
    """ GET and POST /api/assets/<asset_id>/units/ """
    permission_classes = [IsAuthenticated, IsBusinessWorkspace, BelongsToWorkspace]

    def get(self, request, asset_id):
        # 🟢 CHANGED: Validate against request.workspace
        asset = get_object_or_404(Assets, id=asset_id, workspace=request.workspace)
        units = Unit.objects.filter(asset=asset)
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data)

    def post(self, request, asset_id):
        asset = get_object_or_404(Assets, id=asset_id, workspace=request.workspace)

        serializer = CreateUnitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 🟢 CHANGED: Use ModelSerializer to save securely
        unit = serializer.save(asset=asset)

        return Response(UnitSerializer(unit).data, status=status.HTTP_201_CREATED)


class UnitDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ GET, PATCH, DELETE /api/assets/<asset_id>/units/<pk>/ """
    permission_classes = [IsAuthenticated, IsBusinessWorkspace, BelongsToWorkspace]
    serializer_class = UnitSerializer

    def get_queryset(self):
        # 🟢 CHANGED: Traverse the relationship to check workspace
        return Unit.objects.filter(asset__workspace=self.request.workspace)