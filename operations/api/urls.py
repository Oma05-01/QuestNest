# operations/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, TaskViewSet, EventTraceAPIView

app_name = 'operations'
router = DefaultRouter()

# The router automatically builds GET /events/, GET /events/<id>/, etc.
router.register(r'events', EventViewSet, basename='events')
router.register(r'tasks', TaskViewSet, basename='tasks')

urlpatterns = [
    path('', include(router.urls)),
    path('events/<uuid:pk>/trace/', EventTraceAPIView.as_view(), name='event-trace'),
]