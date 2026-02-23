from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Organisation, Membership
from .forms import OrganisationCreateForm
from organisations.permissions import role_required, membership_required


@login_required
def create_organisation(request):
    if request.method == "POST":
        form = OrganisationCreateForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                # Create organisation
                organisation = form.save()

                # Create owner membership
                Membership.objects.create(
                    user=request.user,
                    organisation=organisation,
                    role=Membership.OWNER
                )

            return redirect("organisation_dashboard")

    else:
        form = OrganisationCreateForm()

    return render(request, "organisations/create.html", {"form": form})

@login_required
def select_organisation(request):
    memberships = request.user.memberships.filter(is_active=True)

    if memberships.count() == 0:
        return redirect("tenant_dashboard")

    if memberships.count() == 1:
        org = memberships.first().organisation
        request.session["active_org_id"] = str(org.id)
        return redirect("organisation_dashboard")

    # If multiple
    return render(request, "organisations/select.html", {
        "memberships": memberships
    })

@login_required
def set_active_organisation(request, org_id):
    membership = request.user.memberships.filter(
        organisation_id=org_id,
        is_active=True
    ).first()

    if membership:
        request.session["active_org_id"] = str(membership.organisation.id)

    return redirect("organisation_dashboard")



