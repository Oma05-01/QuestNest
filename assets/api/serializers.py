from rest_framework import serializers
from assets.models import Assets, Unit


class AssetSerializer(serializers.ModelSerializer):
    # 🟢 ADDED: Let the frontend know which workspace this belongs to
    workspace_id = serializers.IntegerField(source='workspace.id', read_only=True)

    class Meta:
        model = Assets
        fields = ['id', 'workspace_id', 'name', 'location', 'status', 'is_verified']
        read_only_fields = ['status', 'is_verified']


class CreateAssetSerializer(serializers.ModelSerializer):
    # 🟢 CHANGED: Switched to ModelSerializer.
    # We do NOT include workspace here because the user shouldn't be able to inject it.
    # We will safely attach the workspace inside the View!
    class Meta:
        model = Assets
        fields = ['name', 'location']


class UnitSerializer(serializers.ModelSerializer):
    # 🟢 ADDED: Helps the frontend know which building this unit is inside
    asset_id = serializers.IntegerField(source='asset.id', read_only=True)

    class Meta:
        model = Unit
        fields = ['id', 'asset_id', 'name', 'status', 'rent_amount']
        read_only_fields = ['status']


class CreateUnitSerializer(serializers.ModelSerializer):
    # 🟢 CHANGED: Switched to ModelSerializer.
    class Meta:
        model = Unit
        fields = ['name', 'rent_amount']