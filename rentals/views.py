from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import TenancyForm
from .models import Tenancy
from organisations.models import Membership


@login_required
def tenancy_create(request):

    if not request.organisation:
        return redirect("create_organisation")

    membership = Membership.objects.filter(
        user=request.user,
        organisation=request.organisation
    ).first()

    if not membership:
        return HttpResponseForbidden("You are not part of this organisation.")

    if membership.role not in ["owner", "manager", "operator"]:
        return HttpResponseForbidden("You do not have permission to create tenancies.")

    if request.method == "POST":
        form = TenancyForm(request.POST)
        if form.is_valid():
            tenancy = form.save(commit=False)
            tenancy.organisation = request.organisation
            tenancy.status = Tenancy.PENDING
            tenancy.save()
            return redirect("tenancy_list")

    else:
        form = TenancyForm()

    return render(request, "rentals/tenancy_form.html", {"form": form})

def tenancy_list(request):
    tenancies = Tenancy.objects.filter(
        organisation=request.organisation
    )
    return render(request, "rentals/tenancy_list.html", {"tenancies": tenancies})