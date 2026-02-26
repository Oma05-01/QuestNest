from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from accounts.models import User
from assets.models import Assets
from wallet.models import Wallet
from user_messages.models import Message
from payments.models import Payment
from organisations.models import Membership

# ----------------- Tenant Dashboard -----------------
@login_required
def tenant_dashboard(request):
    user = request.user
    saved_properties = Assets.objects.filter(saved_by=user)
    wallet = Wallet.objects.filter(user=user).first()
    messages_list = Message.objects.filter(user=user)

    context = {
        'user': user,
        'saved_properties': saved_properties,
        'wallet': wallet,
        'messages': messages_list,
    }
    return render(request, 'dashboard/tenant.html', context)

# ----------------- Landlord Dashboard -----------------
@login_required
def landlord_dashboard(request):
    if not request.organisation:
        return redirect("create_organisation")

    membership = Membership.objects.filter(
        user=request.user,
        organisation=request.organisation
    ).first()
    if not membership or membership.role not in ["owner", "manager"]:
        return HttpResponseForbidden("You do not have access to this dashboard.")

    properties = Assets.objects.filter(organisation=request.organisation)
    payments_list = Payment.objects.filter(assets__organisation=request.organisation)
    messages_list = Message.objects.filter(user=request.user)

    context = {
        'user': request.user,
        'properties': properties,
        'payments': payments_list,
        'messages': messages_list,
    }
    return render(request, 'dashboard/landlord.html', context)

# ----------------- Agent Dashboard -----------------
@login_required
def agent_dashboard(request):
    if not request.organisation:
        return redirect("create_organisation")

    membership = Membership.objects.filter(
        user=request.user,
        organisation=request.organisation
    ).first()
    if not membership or membership.role != "agent":
        return HttpResponseForbidden("You do not have access to this dashboard.")

    managed_properties = Assets.objects.filter(organisation=request.organisation)
    leads = []  # Placeholder for future implementation
    messages_list = Message.objects.filter(user=request.user)

    context = {
        'user': request.user,
        'managed_properties': managed_properties,
        'leads': leads,
        'messages': messages_list,
    }
    return render(request, 'dashboard/agent.html', context)

# ----------------- Admin Dashboard -----------------
@login_required
def admin_dashboard(request):
    if not request.organisation:
        return redirect("create_organisation")

    membership = Membership.objects.filter(
        user=request.user,
        organisation=request.organisation
    ).first()
    if not membership or membership.role != "admin":
        return HttpResponseForbidden("You do not have access to this dashboard.")

    users_list = User.objects.filter(memberships__organisation=request.organisation)
    properties_list = Assets.objects.filter(organisation=request.organisation)
    payments_list = Payment.objects.filter(assets__organisation=request.organisation)
    messages_list = Message.objects.filter(user=request.user)

    context = {
        'user': request.user,
        'users': users_list,
        'properties': properties_list,
        'payments': payments_list,
        'messages': messages_list,
    }
    return render(request, 'dashboard/admin.html', context)
