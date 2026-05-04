from django.urls import path, include

urlpatterns = [
    path("auth/", include("accounts.api.urls")),
    path("assets/", include("assets.api.urls")),
    path("leases/", include("leases.api.urls")),
    path("tenancies/", include("rentals.api.urls")),
    path("payments/", include("payments.api.urls")),
    path("wallet/", include("wallet.api.urls")),
    path("escrows/", include("escrow.api.urls")),
    path("notifications/", include("notifications.api.urls")),
    path("operations/", include("operations.api.urls")),
    path("organisations/", include("organisations.api.urls")),
    path("verification/", include("verification.api.urls")),
    path("messages/", include("user_messages.api.urls")),
    path("dashboard/", include("dashboards.api.urls")),
    path("maintenance/", include("maintenance.api.urls")),

]