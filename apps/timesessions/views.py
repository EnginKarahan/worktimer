from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .services import TimerService
from .exceptions import AlreadyClockedInError, NotClockedInError
from .models import TimeEntry


@login_required
def dashboard(request):
    service = TimerService()
    active = service.get_active_entry(request.user)
    today_entries = TimeEntry.objects.filter(
        user=request.user, date=__import__("django.utils.timezone", fromlist=["now"]).now().date()
    ).order_by("-start_time")
    return render(request, "timesessions/dashboard.html", {
        "active_entry": active,
        "today_entries": today_entries,
    })


@login_required
def timer_view(request):
    service = TimerService()
    active = service.get_active_entry(request.user)
    return render(request, "timesessions/timer.html", {"active_entry": active})


@login_required
def timer_status(request):
    service = TimerService()
    active = service.get_active_entry(request.user)
    if active:
        return render(request, "timesessions/partials/timer_widget.html", {"active_entry": active})
    return render(request, "timesessions/partials/timer_widget.html", {"active_entry": None})


@login_required
@require_POST
def clock_in(request):
    service = TimerService()
    try:
        entry = service.clock_in(request.user)
        messages.success(request, "Eingestempelt!")
    except AlreadyClockedInError:
        messages.warning(request, "Sie sind bereits eingestempelt.")
    return redirect("timesessions:timer")


@login_required
@require_POST
def clock_out(request):
    service = TimerService()
    try:
        entry = service.clock_out(request.user)
        messages.success(request, "Ausgestempelt!")
    except NotClockedInError:
        messages.warning(request, "Kein aktiver Zeiteintrag gefunden.")
    return redirect("timesessions:timer")


@login_required
@require_POST
def pause_view(request):
    service = TimerService()
    try:
        service.pause(request.user)
        messages.success(request, "Pause gestartet.")
    except NotClockedInError:
        messages.warning(request, "Kein laufender Zeiteintrag.")
    return redirect("timesessions:timer")


@login_required
@require_POST
def resume_view(request):
    service = TimerService()
    try:
        service.resume(request.user)
        messages.success(request, "Arbeit fortgesetzt.")
    except NotClockedInError:
        messages.warning(request, "Kein pausierter Zeiteintrag.")
    return redirect("timesessions:timer")


@login_required
def entries_list(request):
    entries = TimeEntry.objects.filter(user=request.user).order_by("-date", "-start_time")
    return render(request, "timesessions/entries.html", {"entries": entries})
