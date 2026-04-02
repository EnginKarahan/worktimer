from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import UserProfile, WorkSchedule, ROLE_CHOICES
from django.utils import timezone


@login_required
@require_POST
def switch_role(request):
    requested = request.POST.get("role", "")
    valid_roles = {r[0] for r in ROLE_CHOICES}
    if requested not in valid_roles:
        messages.error(request, "Ungültige Rolle.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    if request.user.is_superuser:
        allowed = valid_roles
    else:
        allowed = set(request.user.roles.values_list("role", flat=True))

    if requested not in allowed:
        messages.error(request, "Diese Rolle ist Ihnen nicht zugewiesen.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    request.session["active_role"] = requested
    label = dict(ROLE_CHOICES).get(requested, requested)
    messages.success(request, f"Aktive Rolle: {label}")
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    schedules = WorkSchedule.objects.filter(user=request.user).order_by("-effective_from")
    return render(request, "accounts/profile.html", {
        "profile": profile,
        "schedules": schedules,
    })
