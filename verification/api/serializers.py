from rest_framework import serializers


class SubmitVerificationSerializer(serializers.Serializer):
    """
    Handles multi-file uploads for verifying either a
    Business Workspace or a specific Physical Asset.
    """
    # 🟢 UPDATED: Using 'workspace' and 'asset' to match our core apps
    TARGET_CHOICES = [
        ('workspace', 'Workspace'),
        ('asset', 'Asset')
    ]

    target_type = serializers.ChoiceField(choices=TARGET_CHOICES)
    target_id = serializers.UUIDField()

    # 🟢 ADDED: Allows the user to specify what they are uploading
    # (e.g., "Registration Documents" or "Utility Bill")
    document_type = serializers.CharField(max_length=100, required=False)

    # ListField for bulk document uploads
    documents = serializers.ListField(
        child=serializers.FileField(
            max_length=1000000,
            allow_empty_file=False,
            use_url=False
        ),
        allow_empty=False,
        help_text="Upload one or more verification documents (PDF, PNG, JPG)."
    )

    def validate(self, data):
        # You could add logic here to ensure the target_id
        # actually exists in the respective table.
        return data