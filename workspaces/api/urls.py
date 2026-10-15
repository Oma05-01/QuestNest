from django.urls import path
from .views import MyWorkspacesView # 🟢 Updated name

app_name = 'workspaces'

urlpatterns = [
    # 🟢 The "Master Key" to the workspace switcher
    # This returns every workspace the user belongs to (Personal & Business)
    path('', MyWorkspacesView.as_view(), name='workspace-list'),
]