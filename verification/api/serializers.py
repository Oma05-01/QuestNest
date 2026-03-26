from rest_framework import serializers


class SubmitVerificationSerializer(serializers.Serializer):
    # We use a generic serializer that can handle either an org or an asset
    target_type = serializers.ChoiceField(choices=['organisation', 'property'])
    target_id = serializers.UUIDField()

    # ListField allows multiple files to be uploaded at once for properties
    documents = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False
    )