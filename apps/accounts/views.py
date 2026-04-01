from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile, WorkSchedule
from django.utils import timezone


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    schedules = WorkSchedule.objects.filter(user=request.user).order_by("-effective_from")
    return render(request, "accounts/profile.html", {
        "profile": profile,
        "schedules": schedules,
    })
