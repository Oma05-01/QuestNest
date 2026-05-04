from assets.models import Assets, Unit
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from core.api.permissions import IsLandlord, BelongsToOrganisation
from assets.models import Assets
from .serializers import AssetSerializer, CreateAssetSerializer,  UnitSerializer, CreateUnitSerializer

from operations.services.event_service import log_event
from operations.constants import EventType
from ..services.asset_service import create_asset


class AssetListCreateView(APIView):
    """ GET /api/assets/ & POST /api/assets/ """

    def get_permissions(self):
        # Landlords can create, anyone authenticated can read
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsLandlord(), BelongsToOrganisation()]
        return [IsAuthenticated(), BelongsToOrganisation()]

    @extend_schema(summary="List Assets", responses=AssetSerializer(many=True))
    def get(self, request):
        # 🟢 FIX: Filter by Organisation, not by User!
        if request.user.role in ['landlord', 'agent']:
            assets = Assets.objects.filter(organisation=request.user.organisation)
        else:
            # Maybe tenants only see listed ones?
            assets = Assets.objects.filter(status=Assets.LISTED)

        # Optional: Add the search query logic from your old views
        search_query = request.GET.get("q", "")
        if search_query:
            assets = assets.filter(name__icontains=search_query) | assets.filter(location__icontains=search_query)

        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Create Asset", request=CreateAssetSerializer, responses={201: AssetSerializer})
    def post(self, request):
        serializer = CreateAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 🟢 FIX: Call your service layer! Pass the validated data and the organisation.
        asset = create_asset(
            owner=request.user,
            name=serializer.validated_data['name'],
            location=serializer.validated_data['location'],
            organisation=request.user.organisation
        )

        return Response(AssetSerializer(asset).data, status=status.HTTP_201_CREATED)

class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ GET, PATCH, DELETE /api/assets/<pk>/ """

    permission_classes = [IsAuthenticated, IsLandlord, BelongsToOrganisation]
    serializer_class = AssetSerializer

    def get_queryset(self):
        # 🟢 FIX: Ensure landlords can only touch properties in their organisation
        return Assets.objects.filter(organisation=self.request.user.organisation)

    @extend_schema(summary="Update Asset")
    def perform_update(self, serializer):
        asset = self.get_object()

        # Capture old values before saving
        old_values = {field: getattr(asset, field) for field in serializer.validated_data.keys()}

        updated_asset = serializer.save()

        # Capture new values and find differences
        changed_fields = {}
        for field, old_val in old_values.items():
            new_val = getattr(updated_asset, field)
            if old_val != new_val:
                changed_fields[field] = {"old": old_val, "new": new_val}

        # 🟢 FIX: Restore the Audit Log for updates
        if changed_fields:
            log_event(
                organisation=updated_asset.organisation,
                actor=self.request.user,
                event_type=EventType.PROPERTY_UPDATED,
                object_type="Asset",
                object_id=str(updated_asset.id),
                metadata={"changed_fields": changed_fields}
            )

    @extend_schema(summary="Delete Asset")
    def perform_destroy(self, instance):
        # Optional: Add a PROPERTY_DELETED log event here if you want!
        instance.delete()

class UnitListCreateView(APIView):
    """ GET and POST /api/assets/<asset_id>/units/ """
    permission_classes = [IsAuthenticated, IsLandlord, BelongsToOrganisation]

    def get(self, request, asset_id):
        # 1. Ensure the asset belongs to the user's organisation
        asset = get_object_or_404(Assets, id=asset_id, organisation=request.user.organisation)

        # 2. Fetch the units
        units = Unit.objects.filter(asset=asset)
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data)

    def post(self, request, asset_id):
        asset = get_object_or_404(Assets, id=asset_id, organisation=request.user.organisation)

        serializer = CreateUnitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create the unit! (You could also move this to a service layer like create_asset)
        unit = Unit.objects.create(
            asset=asset,
            name=serializer.validated_data['name'],
            rent_amount=serializer.validated_data.get('rent_amount')
        )

        # Optional: log_event for UNIT_CREATED here

        return Response(UnitSerializer(unit).data, status=status.HTTP_201_CREATED)

class UnitDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ GET, PATCH, DELETE /api/assets/<asset_id>/units/<pk>/ """
    permission_classes = [IsAuthenticated, IsLandlord, BelongsToOrganisation]
    serializer_class = UnitSerializer

    def get_queryset(self):
        # Only allow touching units that belong to the user's organisation
        return Unit.objects.filter(asset__organisation=self.request.user.organisation)