from django.urls import path
from .views import EventListView, TaskListView

app_name = 'operations'

urlpatterns = [
    path('events/', EventListView.as_view(), name='event-list'),
    path('tasks/', TaskListView.as_view(), name='task-list'),
]