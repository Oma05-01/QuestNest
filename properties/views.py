from django.shortcuts import render, get_object_or_404, redirect
from .models import Property
from .forms import PropertyForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from accounts.models import User
from organisations.models import Membership
from operations.services.event_service import log_event
from operations.constants import EventType
from organisations.permissions import membership_required, operator_required

# List all properties
@login_required
def property_list(request):

    if not request.organisation:
        return redirect("create_organisation")

    # Only properties in current organisation
    properties = Property.objects.filter(
        is_verified=True,
        organisation__verification__verified=True
    )

    # -------- Search ----------
    search_query = request.GET.get('q', '')
    if search_query:
        properties = properties.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(owner__name__icontains=search_query)
        )

    context = {
        'properties': properties,
        'search_query': search_query,
    }

    return render(request, 'properties/property_list.html', context)

# Property detail view
@login_required
def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk)
    return render(request, 'properties/property_detail.html', {'property': property})

# Create property
@login_required
@membership_required
@operator_required
def property_create(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.organisation:
        return redirect("create_organisation")

    # Get membership inside active organisation
    membership = Membership.objects.filter(
        user=request.user,
        organisation=request.organisation
    ).first()

    if not membership:
        return HttpResponseForbidden("You are not part of this organisation.")

    if membership.role == "tenant":
        return HttpResponseForbidden("Tenants cannot create properties.")

    if not request.organisation.is_verified:
        return HttpResponseForbidden("Your organisation is not verified.")

    # todo: ONLY landlords, admins can create and edit properties
    if request.method == "POST":
        form = PropertyForm(request.POST)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.organisation = request.organisation
            prop.save()

            log_event(
                organisation=request.organisation,
                actor=request.user,
                event_type=EventType.PROPERTY_CREATED,
                object_type="Property",
                object_id=str(prop.id),
                metadata={
                    "property_id": str(prop.id),
                    "property_name": prop.name
                }
            )

            return redirect("property_list")

    else:
        form = PropertyForm()

    return render(request, "properties/property_form.html", {"form": form})


# Edit property
@login_required
@membership_required
@operator_required
def property_edit(request, pk):

    if not request.organisation:
        return redirect("create_organisation")

    prop = get_object_or_404(
        Property,
        pk=pk,
        organisation=request.organisation
    )

    membership = Membership.objects.filter(
        user=request.user,
        organisation=request.organisation
    ).first()

    if not membership:
        return HttpResponseForbidden("Not part of this organisation.")

    if membership.role == "tenant":
        return HttpResponseForbidden("Tenants cannot edit properties.")

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=prop)
        if form.is_valid():
            old_values = {
                field: getattr(prop, field)
                for field in form.changed_data
            }
            updated_property = form.save()
            new_values = {
                field: getattr(updated_property, field)
                for field in form.changed_data
            }

            changed_fields = {}

            for field in form.changed_data:
                changed_fields[field] = {
                    "old": old_values[field],
                    "new": new_values[field],
                }

            log_event(
                organisation=updated_property.organisation,
                actor=request.user,
                event_type=EventType.PROPERTY_UPDATED,
                object_type="Property",
                object_id=str(updated_property.id),
                metadata={
                    "changed_fields": changed_fields
                }
            )
            return redirect('property_list')
    else:
        form = PropertyForm(instance=prop)

    return render(request, 'properties/property_form.html', {'form': form})

# Delete property
@login_required
@membership_required
@operator_required
def property_delete(request, pk):

    if not request.organisation:
        return redirect("create_organisation")

    prop = get_object_or_404(
        Property,
        pk=pk,
        organisation=request.organisation
    )

    membership = Membership.objects.filter(
        user=request.user,
        organisation=request.organisation
    ).first()

    if not membership:
        return HttpResponseForbidden("Not part of this organisation.")

    if membership.role == "tenant":
        return HttpResponseForbidden("You are not allowed to delete properties.")

    if request.method == 'POST':
        prop.delete()
        return redirect('property_list')

    return render(
        request,
        'properties/property_confirm_delete.html',
        {'property': prop}
    )

