from rest_framework import serializers
from ..models import Conversation, Message
from django.utils.timesince import timesince

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
        # Returns a nice format like "10:30 AM"
        return obj.created_at.strftime("%I:%M %p")

class ConversationListSerializer(serializers.ModelSerializer):
    # These explicitly match your React component's mock data keys!
    name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    lastMessage = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    unread = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'role', 'lastMessage', 'time', 'unread', 'avatar']

    def _get_other_user(self, obj):
        request = self.context.get('request')
        if not request: return None
        # Get the first participant that IS NOT the logged-in user
        return obj.participants.exclude(id=request.user.id).first()

    def get_name(self, obj):
        other = self._get_other_user(obj)
        return other.name if other else "Unknown"

    def get_role(self, obj):
        other = self._get_other_user(obj)
        return other.role.title() if other else ""

    def get_avatar(self, obj):
        other = self._get_other_user(obj)
        # Returns the first initial (e.g., "B" for Bayo)
        return other.name[0].upper() if other and other.name else "👤"

    def get_lastMessage(self, obj):
        last_msg = obj.messages.last()
        return last_msg.body if last_msg else "No messages yet."

    def get_time(self, obj):
        last_msg = obj.messages.last()
        if not last_msg: return ""
        # e.g., "2 hours ago" or "10:30 AM"
        return last_msg.created_at.strftime("%b %d, %I:%M %p")

    def get_unread(self, obj):
        request = self.context.get('request')
        if not request: return 0
        # Count messages in this conversation NOT sent by me, and NOT read
        return obj.messages.exclude(sender=request.user).filter(is_read=False).count()