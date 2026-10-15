from rest_framework import serializers
from ..models import Conversation, Message
from workspaces.models import Membership


class MessageSerializer(serializers.ModelSerializer):
    is_me = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    sender_name = serializers.CharField(source='sender.name', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'body', 'is_me', 'time', 'sender_name', 'created_at']

    def get_is_me(self, obj):
        request = self.context.get('request')
        return obj.sender == request.user if request else False

    def get_time(self, obj):
        return obj.created_at.strftime("%I:%M %p")


class ConversationListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()  # 🟢 UPDATED: Workspace-aware role
    lastMessage = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    unread = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    workspace_id = serializers.UUIDField(source='workspace.id', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'workspace_id', 'name', 'role', 'lastMessage', 'time', 'unread', 'avatar']

    def _get_other_user(self, obj):
        request = self.context.get('request')
        if not request: return None
        # Participants are humans; we find the one that isn't the current human
        return obj.participants.exclude(id=request.user.id).first()

    def get_name(self, obj):
        other = self._get_other_user(obj)
        return other.name if other else "System"

    def get_role(self, obj):
        """
        🟢 NEW: Instead of User.role, we check their Membership
        role within the conversation's workspace.
        """
        other = self._get_other_user(obj)
        if not other:
            return "System"

        # Look up what this person is in the context of THIS conversation's workspace
        membership = Membership.objects.filter(
            workspace=obj.workspace,
            user=other
        ).first()

        return membership.get_role_display() if membership else "External"

    def get_avatar(self, obj):
        other = self._get_other_user(obj)
        return other.name[0].upper() if other and other.name else "👤"

    def get_lastMessage(self, obj):
        last_msg = obj.messages.last()
        return last_msg.body if last_msg else "No messages yet."

    def get_time(self, obj):
        last_msg = obj.messages.last()
        if not last_msg: return ""
        # Format: "May 12, 10:30 AM"
        return last_msg.created_at.strftime("%b %d, %I:%M %p")

    def get_unread(self, obj):
        request = self.context.get('request')
        if not request: return 0
        return obj.messages.exclude(sender=request.user).filter(is_read=False).count()