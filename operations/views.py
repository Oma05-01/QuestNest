from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from .models import Event, Task
from organisations.models import Membership
from organisations.permissions import membership_required, operator_required, roles_required, role_required
from django.shortcuts import render

@login_required
@membership_required
@roles_required
@role_required(["owner", "manager"])
def organisation_audit_timeline(request):

    if not request.organisation:
        return JsonResponse({"error": "No organisation selected"}, status=400)

    membership = Membership.objects.filter(
        user=request.user,
        organisation=request.organisation
    ).first()

    if not membership or membership.role not in ["owner", "admin"]:
        return JsonResponse({"error": "Not allowed"}, status=403)

    events = Event.objects.filter(
        organisation=request.organisation
    ).order_by("-created_at")[:100]

    data = []

    for event in events:
        data.append({
            "event_type": event.event_type,
            "actor": event.actor.name if event.actor else "System",
            "object_type": event.object_type,
            "object_id": event.object_id,
            "metadata": event.metadata,
            "created_at": event.created_at,
        })

    return JsonResponse({"events": data})


@login_required
@membership_required
@roles_required
def admin_audit_timeline(request):

    if not request.organisation:
        return HttpResponseForbidden("No active organisation.")

    events = Event.objects.filter(
        organisation=request.organisation
    ).order_by("-created_at")

    tasks = Task.objects.filter(
        organisation=request.organisation
    ).order_by("-created_at")

    context = {
        "events": events,
        "tasks": tasks
    }

    return render(request, "operations/admin_audit_timeline.html", context)


def admin_timeline(request):

    if not request.organisation:
        return JsonResponse({"error": "No organisation selected"}, status=400)

    events = Event.objects.filter(
        organisation=request.organisation
    ).order_by("-created_at")[:100]

    data = []

    for event in events:
        data.append({
            "event_type": event.event_type,
            "actor": event.actor.name if event.actor else "System",
            "object_type": event.object_type,
            "object_id": event.object_id,
            "metadata": event.metadata,
            "created_at": event.created_at,
        })

    return JsonResponse({
        "timeline": data
    })