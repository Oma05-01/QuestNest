from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from user_messages.models import Message
from user_messages.services.message_service import create_message
from .serializers import MessageSerializer, CreateMessageSerializer

class MessageListView(APIView):
    """ GET /api/messages/ & POST /api/messages/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Users only see messages associated with their account
        messages = Message.objects.filter(user=request.user).order_by('-created_at')
        return Response(MessageSerializer(messages, many=True).data)

    def post(self, request):
        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = create_message(
            user=request.user,
            content=serializer.validated_data['content']
        )

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)