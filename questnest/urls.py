from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [

    # Api Gateway
    path("api/", include("core.api.urls")),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('admin/', admin.site.urls),

    # Web routes
    path("accounts/", include("accounts.urls")),
    path("dashboards/", include("dashboards.urls")),
    path('assets/', include('assets.urls')),
    path('escrow/', include('escrow.urls')),
    path('payments/', include('payments.urls')),
    path('messages/', include('user_messages.urls')),
    path('wallet/', include('wallet.urls')),
    path("organisations/", include("organisations.urls")),
    path("verification/", include("verification.urls")),
    path("operations/", include("operations.urls")),
    path("tenancies/", include("rentals.urls")),


    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
