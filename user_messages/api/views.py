from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from core.api.permissions import IsWorkspaceMember, BelongsToWorkspace
from workspaces.models import Membership
from ..models import Conversation, Message
from .serializers import ConversationListSerializer, MessageSerializer


class InboxView(APIView):
    """ GET /api/chat/inbox/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get(self, request):
        # 🟢 Filter by participant AND active workspace
        conversations = Conversation.objects.filter(
            participants=request.user,
            workspace=request.workspace
        ).prefetch_related('participants', 'messages').order_by('-updated_at')

        serializer = ConversationListSerializer(
            conversations, many=True, context={'request': request}
        )
        return Response(serializer.data)


class ChatDetailView(APIView):
    """ GET /api/chat/<id>/messages/ & POST """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get(self, request, pk):
        # 🛡️ Ensure the chat belongs to the user AND this specific workspace context
        conversation = get_object_or_404(
            Conversation,
            pk=pk,
            participants=request.user,
            workspace=request.workspace
        )

        # Mark unread messages from the other person as read
        conversation.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

        messages = conversation.messages.all().order_by('created_at')
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, pk):
        conversation = get_object_or_404(
            Conversation,
            pk=pk,
            participants=request.user,
            workspace=request.workspace
        )
        body = request.data.get('body')

        if not body:
            return Response({"error": "Message body cannot be empty."}, status=400)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            body=body
        )

        # Update timestamp to float conversation to top of inbox
        conversation.save()

        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=201)


class StartConversationView(APIView):
    """ POST /api/chat/start/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def post(self, request):
        target_user_id = request.data.get('user_id')

        # 🛡️ Security Check: Is the target user actually a member of this workspace?
        membership = get_object_or_404(
            Membership,
            workspace=request.workspace,
            user_id=target_user_id,
            is_active=True
        )
        target_user = membership.user

        # 1. Check for existing 1-on-1 chat within THIS workspace
        existing_conv = Conversation.objects.filter(
            workspace=request.workspace,
            participants=request.user
        ).filter(participants=target_user).first()

        if existing_conv:
            return Response({"id": existing_conv.id, "message": "Conversation exists"}, status=200)

        # 2. Create a new conversation locked to this workspace
        new_conv = Conversation.objects.create(workspace=request.workspace)
        new_conv.participants.add(request.user, target_user)

        return Response({"id": new_conv.id, "message": "Conversation created"}, status=201)


class AvailableContactsView(APIView):
    """ GET /api/chat/contacts/ """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]

    def get(self, request):
        """
        🟢 NEW LOGIC: Lists everyone in the current workspace except yourself.
        This automatically handles Tenants seeing Landlords and vice-versa
        based on who else is in the 'Membership' list.
        """
        memberships = Membership.objects.filter(
            workspace=request.workspace,
            is_active=True
        ).exclude(user=request.user).select_related('user')

        contacts = []
        for m in memberships:
            contacts.append({
                "id": m.user.id,
                "name": m.user.name or m.user.email,
                "role": m.get_role_display(),  # e.g., "Owner", "Manager", "Tenant"
                "avatar": m.user.name[0].upper() if m.user.name else "👤"
            })

        return Response(contacts)