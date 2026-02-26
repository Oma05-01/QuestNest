"""
URL configuration for questnest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
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

]
