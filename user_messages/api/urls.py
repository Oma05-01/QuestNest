from django.urls import path
from .views import (
    InboxView, ChatDetailView,
    StartConversationView, AvailableContactsView
)

app_name = 'chat'

urlpatterns = [
    path('inbox/', InboxView.as_view(), name='inbox'),
    path('contacts/', AvailableContactsView.as_view(), name='contacts'),
    path('start/', StartConversationView.as_view(), name='start-chat'),
    path('<uuid:pk>/messages/', ChatDetailView.as_view(), name='chat-detail'),
]