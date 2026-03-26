from django.urls import path
from .views import AssetListView

app_name = 'assets'

urlpatterns = [
    # GET  /api/assets/ (Lists properties)
    # POST /api/assets/ (Creates a new property)
    path('', AssetListView.as_view(), name='asset-list'),

    # NOTE: When you are ready to build the specific property view (PATCH/GET /api/assets/{id}/),
    # it will go right here like this:
    # path('<uuid:pk>/', AssetDetailView.as_view(), name='asset-detail'),
]