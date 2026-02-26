from django.shortcuts import render, get_object_or_404, redirect
from .models import Assets
from .forms import AssetsForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from organisations.models import Membership
from operations.services.event_service import log_event
from operations.constants import EventType
from organisations.permissions import membership_required, operator_required

# List all properties
@login_required
def asset_list(request):

    if not request.organisation:
        return redirect("create_organisation")

    assets = Assets.objects.filter(
        organisation=request.organisation
    )

    search_query = request.GET.get("q", "")
    if search_query:
        assets = assets.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    context = {
        "assets": assets,
        "search_query": search_query,
    }

    return render(request, "assets/asset_list.html", context)

# Property detail view
@login_required
def asset_detail(request, pk):

    if not request.organisation:
        return redirect("create_organisation")

    asset = get_object_or_404(
        Assets,
        pk=pk,
        organisation=request.organisation
    )

    return render(request, "assets/asset_detail.html", {"asset": asset})

# Create property
@login_required
@membership_required
@operator_required
def asset_create(request):

    if not request.organisation:
        return redirect("create_organisation")

    if request.method == "POST":
        form = AssetsForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.organisation = request.organisation
            asset.save()

            log_event(
                organisation=request.organisation,
                actor=request.user,
                event_type=EventType.PROPERTY_CREATED,
                object_type="Asset",
                object_id=str(asset.id),
                metadata={
                    "asset_name": asset.name
                }
            )

            return redirect("asset_list")

    else:
        form = AssetsForm()

    return render(request, "assets/asset_form.html", {"form": form})


# Edit property
@login_required
@membership_required
@operator_required
def asset_edit(request, pk):

    if not request.organisation:
        return redirect("create_organisation")

    asset = get_object_or_404(
        Assets,
        pk=pk,
        organisation=request.organisation
    )

    if request.method == "POST":
        form = AssetsForm(request.POST, instance=asset)
        if form.is_valid():

            old_values = {
                field: getattr(asset, field)
                for field in form.changed_data
            }

            updated_asset = form.save()

            new_values = {
                field: getattr(updated_asset, field)
                for field in form.changed_data
            }

            changed_fields = {
                field: {
                    "old": old_values[field],
                    "new": new_values[field]
                }
                for field in form.changed_data
            }

            log_event(
                organisation=updated_asset.organisation,
                actor=request.user,
                event_type=EventType.PROPERTY_UPDATED,
                object_type="Asset",
                object_id=str(updated_asset.id),
                metadata={"changed_fields": changed_fields}
            )

            return redirect("asset_list")

    else:
        form = AssetsForm(instance=asset)

    return render(request, "assets/asset_form.html", {"form": form})

# Delete property
@login_required
@membership_required
@operator_required
def asset_delete(request, pk):

    if not request.organisation:
        return redirect("create_organisation")

    asset = get_object_or_404(
        Assets,
        pk=pk,
        organisation=request.organisation
    )

    if request.method == "POST":
        asset.delete()
        return redirect("asset_list")

    return render(
        request,
        "assets/asset_confirm_delete.html",
        {"asset": asset}
    )

