from django.urls import path
from .views import AssetListCreateView, AssetDetailView, UnitListCreateView, UnitDetailView

app_name = 'assets'

urlpatterns = [
    # 🟢 Lists assets for the CURRENT workspace (Personal or Business)
    path('', AssetListCreateView.as_view(), name='asset-list-create'),

    # 🟢 Detail view gated by the 'BelongsToWorkspace' permission
    path('<uuid:pk>/', AssetDetailView.as_view(), name='asset-detail'),

    # 🟢 Nested units - automatically filtered by the workspace context in the view
    path('<uuid:asset_id>/units/', UnitListCreateView.as_view(), name='unit-list-create'),

    path('<uuid:asset_id>/units/<uuid:pk>/', UnitDetailView.as_view(), name='unit-detail'),
]