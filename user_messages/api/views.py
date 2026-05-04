from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from ..models import Conversation, Message
from .serializers import ConversationListSerializer, MessageSerializer


class InboxView(APIView):
    """ GET /api/chat/inbox/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch conversations where the user is a participant
        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'messages')

        serializer = ConversationListSerializer(
            conversations, many=True, context={'request': request}
        )
        return Response(serializer.data)


class ChatDetailView(APIView):
    """ GET /api/chat/<id>/messages/ & POST """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)

        # Mark unread messages from the other person as read!
        conversation.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)
        body = request.data.get('body')

        if not body:
            return Response({"error": "Message body cannot be empty."}, status=400)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            body=body
        )

        # Bump the conversation's updated_at timestamp so it jumps to the top of the inbox
        conversation.save()

        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=201)

User = get_user_model()


class StartConversationView(APIView):
    """ POST /api/messages/start/ """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        target_user_id = request.data.get('user_id')
        target_user = get_object_or_404(User, id=target_user_id)

        # 1. Check if a conversation already exists between these two exact users
        # (Assuming 1-on-1 chats for now)
        existing_conv = Conversation.objects.filter(participants=request.user) \
            .filter(participants=target_user).first()

        if existing_conv:
            return Response({"id": existing_conv.id, "message": "Conversation exists"}, status=200)

        # 2. If not, create a new one
        new_conv = Conversation.objects.create()
        new_conv.participants.add(request.user, target_user)

        return Response({"id": new_conv.id, "message": "Conversation created"}, status=201)


class AvailableContactsView(APIView):
    """ GET /api/messages/contacts/ """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        contacts = []

        if user.role == 'tenant':
            # Tenant can message the Landlord/Admins of the system/organisation
            # Adjust the filter here based on how you link tenants to landlords
            landlords = User.objects.filter(role__in=['landlord', 'admin'])
            for l in landlords:
                contacts.append({"id": l.id, "name": l.name, "role": "Property Manager"})

        elif user.role in ['landlord', 'admin']:
            # Landlords can message their Tenants
            # (Assuming you filter by organisation in a real production app)
            tenants = User.objects.filter(role='tenant')
            for t in tenants:
                contacts.append({"id": t.id, "name": t.name, "role": "Tenant"})

        return Response(contacts)