from rest_framework import serializers
from assets.models import Assets

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = ['id', 'name', 'location', 'status', 'is_verified']
        read_only_fields = ['status', 'is_verified']

class CreateAssetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    location = serializers.CharField()
    # Add other required fields here if needed