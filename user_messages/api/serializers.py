from rest_framework import serializers
from user_messages.models import Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'created_at']


class CreateMessageSerializer(serializers.Serializer):
    content = serializers.CharField(
        error_messages={"blank": "Message content cannot be empty."}
    )