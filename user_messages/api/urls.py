from django.urls import path
from .views import InboxView, ChatDetailView, StartConversationView, AvailableContactsView

urlpatterns = [
    # 📥 List all conversations for the sidebar
    path('inbox/', InboxView.as_view(), name='chat-inbox'),

    # 💬 Get messages for a specific chat, or send a new one
    path('<int:pk>/messages/', ChatDetailView.as_view(), name='chat-detail'),

    path('start/', StartConversationView.as_view(), name='start-chat'),

    path('contacts/', AvailableContactsView.as_view(), name='chat-contacts')
]