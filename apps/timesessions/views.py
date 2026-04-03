from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .services import TimerService, CorrectionService
from .exceptions import AlreadyClockedInError, NotClockedInError, CorrectionWindowError
from .models import TimeEntry


@login_required
def dashboard(request):
    from django.utils.timezone import now
    from apps.absences.services import calculate_vacation_entitlement, ApprovalService
    from apps.overtime.services import OvertimeCalculator
    from apps.hr.services import SollIstCalculator
    service = TimerService()
    active = service.get_active_entry(request.user)
    today = now().date()
    today_entries = TimeEntry.objects.filter(
        user=request.user, date=today
    ).order_by("-start_time")
    year = today.year
    vac_entitlement = calculate_vacation_entitlement(request.user, year)
    vac_balance = ApprovalService()._get_vacation_balance(request.user, year=year)
    settled_balance = OvertimeCalculator().get_balance_minutes(request.user)
    current_month_data = SollIstCalculator().calculate_monthly_hours(request.user, year, today.month)
    ot_balance = settled_balance + current_month_data["balance_minutes"]
    return render(request, "timesessions/dashboard.html", {
        "active_entry": active,
        "today_entries": today_entries,
        "vacation_entitlement": vac_entitlement,
        "vacation_balance": vac_balance,
        "ot_balance_hours": round(ot_balance / 60, 1),
        "year": year,
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


@login_required
def correct_entry(request, pk):
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    import datetime

    entry = get_object_or_404(TimeEntry, pk=pk, user=request.user)
    service = CorrectionService()
    max_days = service.get_max_correction_days(request.user)

    if request.method == "POST":
        try:
            new_start_str = request.POST.get("start_time")
            new_end_str = request.POST.get("end_time")
            reason = request.POST.get("reason", "").strip()
            if not reason:
                messages.error(request, "Bitte geben Sie eine Begründung an.")
                return redirect("timesessions:correct_entry", pk=pk)

            tz = timezone.get_current_timezone()
            new_start = timezone.make_aware(
                datetime.datetime.fromisoformat(new_start_str), tz
            )
            new_end = timezone.make_aware(
                datetime.datetime.fromisoformat(new_end_str), tz
            )
            if new_end <= new_start:
                messages.error(request, "Endzeit muss nach der Startzeit liegen.")
                return redirect("timesessions:correct_entry", pk=pk)

            service.correct_entry(request.user, entry, new_start, new_end, reason)
            messages.success(request, "Zeiteintrag wurde korrigiert.")
            return redirect("timesessions:entries")
        except CorrectionWindowError as e:
            messages.error(request, str(e))
            return redirect("timesessions:entries")

    earliest = None
    if max_days is not None:
        earliest = (timezone.now().date() - datetime.timedelta(days=max_days)).isoformat()

    return render(request, "timesessions/correct_entry.html", {
        "entry": entry,
        "max_days": max_days,
        "earliest_date": earliest,
    })
