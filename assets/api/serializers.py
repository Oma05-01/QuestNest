from assets.models import Assets
from rest_framework import serializers
from assets.models import Unit

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = ['id', 'name', 'location', 'status', 'is_verified']
        read_only_fields = ['status', 'is_verified']

class CreateAssetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    location = serializers.CharField()
    # Add other required fields here if needed

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name', 'status', 'rent_amount']
        read_only_fields = ['status'] # Status should be managed by lifecycle events!

class CreateUnitSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    rent_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)