from rest_framework import serializers
from workspaces.models import Workspace, Membership


class WorkspaceSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()
    is_personal = serializers.SerializerMethodField() # 🟢 ADDED: Compute this on the fly

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'workspace_type', 'is_verified', 'is_personal', 'my_role']

    def get_my_role(self, obj):
        user = self.context['request'].user
        membership = obj.members.filter(user=user, is_active=True).first()
        return membership.role if membership else None

    def get_is_personal(self, obj):
        # 🟢 Evaluates to True if workspace_type is 'personal', False otherwise
        return obj.workspace_type == Workspace.PERSONAL


class CreateWorkspaceSerializer(serializers.ModelSerializer):
    """
    Used when a user wants to start a new Property Management business
    or setup a new legal entity.
    """
    class Meta:
        model = Workspace
        fields = ['name']

    def create(self, validated_data):
        # Business workspaces are always created as 'business' type through this serializer
        # Personal workspaces are only created during the Registration phase.
        return Workspace.objects.create(
            name=validated_data['name'],
            workspace_type=Workspace.BUSINESS
        )

class MembershipSerializer(serializers.ModelSerializer):
    """
    Used to list team members within a Business Workspace.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user_email', 'user_name', 'role', 'joined_at']