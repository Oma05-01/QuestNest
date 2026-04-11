from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.api.permissions import IsLandlord, BelongsToOrganisation
from assets.models import Assets
from assets.services.asset_service import create_asset
from .serializers import AssetSerializer, CreateAssetSerializer


class AssetListView(APIView):
    """ GET /api/assets/ & POST /api/assets/ """

    def get_permissions(self):
        # Landlords can create, anyone authenticated can read (if we want tenants to see listings later)
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsLandlord(), BelongsToOrganisation()]
        return [IsAuthenticated()]

    def get(self, request):
        if request.user.role == 'landlord':
            assets = Assets.objects.filter(owner=request.user)
        else:
            assets = Assets.objects.filter(status=Assets.LISTED)

        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CreateAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        asset = create_asset(
            owner=request.user,
            name=serializer.validated_data['name'],
            location=serializer.validated_data['location'],
            # Optional: pass request.user.organisation if they belong to one
        )

        return Response(AssetSerializer(asset).data, status=status.HTTP_201_CREATED)