from django.contrib import admin
from .models import Organisation


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    # 🟢 What shows up in the columns on the main list page
    list_display = ('id', 'name', 'is_verified')

    # 🟢 Adds a filter box on the right side to quickly find unverified orgs
    list_filter = ('is_verified',)

    # 🟢 Adds a search bar at the top to search by name
    search_fields = ('name',)

    # 🟢 THE BEST PART: Allows you to check/uncheck 'is_verified'
    # directly from the list view without opening the record!
    list_editable = ('is_verified',)

    # 🟢 Default sorting (alphabetical by name)
    ordering = ('name',)

    # Optional: If you have created_at/updated_at fields, you can make them read-only
    # readonly_fields = ('created_at', 'updated_at')


from django.contrib import admin

# Register your models here.
