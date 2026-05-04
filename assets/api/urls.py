from django.urls import path
from .views import AssetListCreateView, AssetDetailView, UnitListCreateView, UnitDetailView

urlpatterns = [
    path('', AssetListCreateView.as_view(), name='asset-list-create'),
    path('<uuid:pk>/', AssetDetailView.as_view(), name='asset-detail'),
    path('<uuid:asset_id>/units/', UnitListCreateView.as_view(), name='unit-list-create'),
    path('<uuid:asset_id>/units/<uuid:pk>/', UnitDetailView.as_view(), name='unit-detail'),
]