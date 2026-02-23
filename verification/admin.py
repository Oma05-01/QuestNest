from django.contrib import admin
from .models import OrganisationVerification, PropertyVerification, VerificationDocument

@admin.register(OrganisationVerification)
class OrganisationVerificationAdmin(admin.ModelAdmin):
    list_display = ("organisation", "verified", "submitted_at", "verified_at", "reviewed_by")
    list_filter = ("verified",)

@admin.register(PropertyVerification)
class PropertyVerificationAdmin(admin.ModelAdmin):
    list_display = ("property", "verified", "verified_at", "reviewed_by")
    list_filter = ("verified",)
    filter_horizontal = ("documents",)
