import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from apps.absences.models import AbsenceRequest
from apps.absences.services import ApprovalService
from apps.core.models import AuditLog
from apps.core.permissions import hr_required
from apps.overtime.services import OvertimeCalculator
from apps.timesessions.models import TimeEntry
from apps.timesessions.services import CorrectionService
from apps.timesessions.exceptions import CorrectionWindowError
from .forms import (
    EmployeeUserForm,
    EmployeeProfileForm,
    SickLeaveForm,
    AbsenceRejectForm,
)
from .forms import WorkScheduleForm, TimeEntryCreateForm, TimeEntryDeleteForm
from .forms import VacationAdjustmentForm, OvertimeAdjustmentForm
from .services import (
    AdjustmentService,
    TimeEntryHRService,
    SollIstCalculator,
    VacationBalanceService,
)
from apps.accounts.models import WorkSchedule
from apps.timesessions.models import DeletedTimeEntry

User = get_user_model()


@hr_required
def hr_dashboard(request):
    today = timezone.now().date()

    today_absences = AbsenceRequest.objects.filter(
        status="APPROVED",
        start_date__lte=today,
        end_date__gte=today,
    ).select_related("user", "leave_type")

    pending_requests = (
        AbsenceRequest.objects.filter(status="PENDING")
        .select_related("user", "leave_type")
        .order_by("-created_at")[:20]
    )

    clocked_in = (
        TimeEntry.objects.filter(status="RUNNING")
        .select_related("user")
        .order_by("start_time")
    )

    calculator = OvertimeCalculator()
    active_users = User.objects.filter(is_active=True).select_related("userprofile")
    deficit_users = []
    high_overtime_users = []
    for u in active_users:
        balance = calculator.get_balance_minutes(u)
        if balance < 0:
            deficit_users.append({"user": u, "balance_hours": round(balance / 60, 1)})
        elif balance > 40 * 60:
            high_overtime_users.append(
                {"user": u, "balance_hours": round(balance / 60, 1)}
            )

    return render(
        request,
        "hr/dashboard.html",
        {
            "today_absences": today_absences,
            "pending_requests": pending_requests,
            "clocked_in": clocked_in,
            "deficit_users": deficit_users,
            "high_overtime_users": high_overtime_users,
            "today": today,
        },
    )


@hr_required
def employee_list(request):
    employees = (
        User.objects.filter(is_active=True)
        .select_related("userprofile")
        .order_by("last_name", "first_name")
    )
    return render(request, "hr/employee_list.html", {"employees": employees})


@hr_required
def employee_create(request):
    user_form = EmployeeUserForm(request.POST or None)
    profile_form = EmployeeProfileForm(request.POST or None)
    if request.method == "POST":
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            username = (
                user.first_name[:1] + user.last_name
            ).lower() or user.email.split("@")[0]
            base = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{counter}"
                counter += 1
            user.username = username
            user.set_unusable_password()
            user.save()
            profile = user.userprofile
            for field, value in profile_form.cleaned_data.items():
                setattr(profile, field, value)
            profile.save()
            AuditLog.log(
                request.user,
                "employee_created",
                user,
                new={"username": user.username, "email": user.email},
                request=request,
            )
            messages.success(request, f"Mitarbeiter {user.get_full_name()} angelegt.")
            return redirect("hr:employee_list")
    return render(
        request,
        "hr/employee_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "title": "Neuer Mitarbeiter",
        },
    )


@hr_required
def employee_detail(request, pk):
    employee = get_object_or_404(User, pk=pk)
    today = timezone.now().date()
    year = today.year
    # Live balance: settled transactions + unsettled current month
    calculator = OvertimeCalculator()
    settled_balance = calculator.get_balance_minutes(employee)
    current_month_data = SollIstCalculator().calculate_monthly_hours(employee, year, today.month)
    balance = settled_balance + current_month_data["balance_minutes"]
    current_absence = AbsenceRequest.objects.filter(
        user=employee,
        status="APPROVED",
        start_date__lte=today,
        end_date__gte=today,
    ).first()
    active_entry = TimeEntry.objects.filter(
        user=employee, status__in=["RUNNING", "PAUSED"]
    ).first()
    recent_absences = AbsenceRequest.objects.filter(user=employee).order_by(
        "-start_date"
    )[:10]
    from apps.absences.services import calculate_vacation_entitlement, ApprovalService

    vac_entitlement = calculate_vacation_entitlement(employee, year)
    vac_balance = ApprovalService()._get_vacation_balance(employee, year=year)
    return render(
        request,
        "hr/employee_detail.html",
        {
            "employee": employee,
            "balance_hours": round(balance / 60, 1),
            "current_absence": current_absence,
            "active_entry": active_entry,
            "recent_absences": recent_absences,
            "vacation_entitlement": vac_entitlement,
            "vacation_balance": vac_balance,
            "year": year,
        },
    )


@hr_required
def employee_edit(request, pk):
    employee = get_object_or_404(User, pk=pk)
    profile = employee.userprofile
    schedule = (
        WorkSchedule.objects.filter(user=employee).order_by("-effective_from").first()
    )
    old_data = {
        f: getattr(profile, f)
        for f in [
            "employment_type",
            "weekly_work_hours",
            "annual_leave_days",
            "hire_date",
            "federal_state",
            "phone",
            "department",
        ]
    }
    user_form = EmployeeUserForm(request.POST or None, instance=employee)
    profile_form = EmployeeProfileForm(request.POST or None, instance=profile)
    schedule_form = WorkScheduleForm(request.POST or None, instance=schedule)
    if request.method == "POST":
        if user_form.is_valid() and profile_form.is_valid() and schedule_form.is_valid():
            user_form.save()
            profile_form.save()
            saved_schedule = schedule_form.save(commit=False)
            saved_schedule.user = employee
            saved_schedule.save()
            AuditLog.log(
                request.user,
                "employee_updated",
                employee,
                old={k: str(v) for k, v in old_data.items()},
                new={f: str(getattr(profile, f)) for f in old_data},
                request=request,
            )
            messages.success(request, "Profil aktualisiert.")
            return redirect("hr:employee_detail", pk=pk)
    return render(
        request,
        "hr/employee_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "schedule_form": schedule_form,
            "employee": employee,
            "title": f"Mitarbeiter bearbeiten: {employee.get_full_name()}",
        },
    )


@hr_required
def employee_delete(request, pk):
    employee = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        employee.is_active = False
        employee.save()
        AuditLog.log(request.user, "employee_deactivated", employee, request=request)
        messages.success(request, f"{employee.get_full_name()} wurde deaktiviert.")
        return redirect("hr:employee_list")
    return render(request, "hr/employee_confirm_delete.html", {"employee": employee})


@hr_required
def employee_entries(request, pk):
    employee = get_object_or_404(User, pk=pk)
    entries = TimeEntry.objects.filter(user=employee).order_by("-date", "-start_time")
    return render(
        request,
        "hr/employee_entries.html",
        {
            "employee": employee,
            "entries": entries,
        },
    )


@hr_required
def employee_correct_entry(request, pk, entry_pk):
    employee = get_object_or_404(User, pk=pk)
    entry = get_object_or_404(TimeEntry, pk=entry_pk, user=employee)
    service = CorrectionService()

    if request.method == "POST":
        try:
            new_start_str = request.POST.get("start_time")
            new_end_str = request.POST.get("end_time")
            reason = request.POST.get("reason", "").strip()
            if not reason:
                messages.error(request, "Bitte geben Sie eine Begründung an.")
                return redirect("hr:employee_correct_entry", pk=pk, entry_pk=entry_pk)

            tz = timezone.get_current_timezone()
            new_start = timezone.make_aware(
                datetime.datetime.fromisoformat(new_start_str), tz
            )
            new_end = timezone.make_aware(
                datetime.datetime.fromisoformat(new_end_str), tz
            )
            if new_end <= new_start:
                messages.error(request, "Endzeit muss nach der Startzeit liegen.")
                return redirect("hr:employee_correct_entry", pk=pk, entry_pk=entry_pk)

            service.correct_entry(request.user, entry, new_start, new_end, reason)
            messages.success(request, "Zeiteintrag wurde korrigiert.")
            return redirect("hr:employee_entries", pk=pk)
        except CorrectionWindowError as e:
            messages.error(request, str(e))
            return redirect("hr:employee_entries", pk=pk)

    max_days = service.get_max_correction_days(request.user)
    earliest = None
    if max_days is not None:
        earliest = (
            timezone.now().date() - datetime.timedelta(days=max_days)
        ).isoformat()

    return render(
        request,
        "hr/correct_entry.html",
        {
            "employee": employee,
            "entry": entry,
            "max_days": max_days,
            "earliest_date": earliest,
        },
    )


@hr_required
def employee_absences(request, pk):
    employee = get_object_or_404(User, pk=pk)
    absences = AbsenceRequest.objects.filter(user=employee).order_by("-start_date")
    return render(
        request,
        "hr/employee_absences.html",
        {
            "employee": employee,
            "absences": absences,
        },
    )


@hr_required
def enter_sick_leave(request, pk):
    employee = get_object_or_404(User, pk=pk)
    form = SickLeaveForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        service = ApprovalService()
        try:
            service.enter_sick_leave_for_employee(
                hr_user=request.user,
                employee=employee,
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
            )
            messages.success(request, "Krankmeldung wurde eingetragen.")
            return redirect("hr:employee_absences", pk=pk)
        except Exception as e:
            messages.error(request, str(e))
    return render(
        request,
        "hr/enter_sick_leave.html",
        {
            "employee": employee,
            "form": form,
        },
    )


@hr_required
def pending_approvals(request):
    requests = (
        AbsenceRequest.objects.filter(status="PENDING")
        .select_related("user", "leave_type")
        .order_by("-created_at")
    )
    return render(request, "hr/pending_approvals.html", {"requests": requests})


@hr_required
def approve_absence(request, pk):
    absence = get_object_or_404(AbsenceRequest, pk=pk, status="PENDING")
    if request.method == "POST":
        comment = request.POST.get("comment", "")
        ApprovalService().approve(absence, request.user, comment, http_request=request)
        messages.success(request, "Antrag genehmigt.")
    return redirect("hr:pending_approvals")


@hr_required
def reject_absence(request, pk):
    absence = get_object_or_404(AbsenceRequest, pk=pk, status="PENDING")
    form = AbsenceRejectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ApprovalService().reject(
            absence,
            request.user,
            form.cleaned_data.get("comment", ""),
            http_request=request,
        )
        messages.success(request, "Antrag abgelehnt.")
        return redirect("hr:pending_approvals")
    return render(request, "hr/reject_absence.html", {"absence": absence, "form": form})


@hr_required
@ratelimit(key="user", rate="10/m", block=True)
def download_employee_pdf(request, user_pk):
    from apps.reports.services.pdf_service import generate_monthly_pdf
    from django.utils.timezone import now as tz_now

    employee = get_object_or_404(User, pk=user_pk)
    year = int(request.GET.get("year", tz_now().year))
    month = int(request.GET.get("month", tz_now().month))
    pdf = generate_monthly_pdf(employee, year, month)
    AuditLog.log(
        request.user,
        "report_downloaded",
        employee,
        new={"format": "pdf", "year": year, "month": month},
        request=request,
    )
    filename = f"arbeitszeitnachweis_{year}_{month:02d}_{employee.username}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@hr_required
@ratelimit(key="user", rate="10/m", block=True)
def download_employee_excel(request, user_pk):
    from apps.reports.services.excel_service import generate_monthly_excel
    from django.utils.timezone import now as tz_now

    employee = get_object_or_404(User, pk=user_pk)
    year = int(request.GET.get("year", tz_now().year))
    month = int(request.GET.get("month", tz_now().month))
    data = generate_monthly_excel(employee, year, month)
    AuditLog.log(
        request.user,
        "report_downloaded",
        employee,
        new={"format": "excel", "year": year, "month": month},
        request=request,
    )
    filename = f"arbeitszeitnachweis_{year}_{month:02d}_{employee.username}.xlsx"
    response = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# === NEUE HR FEATURE VIEWS ===


@hr_required
def employee_schedule(request, pk):
    """WorkSchedule bearbeiten für einen Mitarbeiter."""
    employee = get_object_or_404(User, pk=pk)
    schedule = (
        WorkSchedule.objects.filter(user=employee).order_by("-effective_from").first()
    )

    if request.method == "POST":
        form = WorkScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = employee
            schedule.save()
            AuditLog.log(
                request.user,
                "work_schedule_updated",
                schedule,
                new={"effective_from": str(schedule.effective_from)},
                request=request,
            )
            messages.success(request, "Arbeitszeitplan aktualisiert.")
            return redirect("hr:employee_detail", pk=pk)
    else:
        form = WorkScheduleForm(instance=schedule)

    weekly_hours = form.weekly_hours if schedule else 40.0

    return render(
        request,
        "hr/employee_schedule.html",
        {
            "employee": employee,
            "form": form,
            "weekly_hours": weekly_hours,
        },
    )


@hr_required
def entry_create(request, pk):
    """Neuen Zeiteintrag für Mitarbeiter anlegen."""
    employee = get_object_or_404(User, pk=pk)
    form = TimeEntryCreateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        service = TimeEntryHRService()
        entry = service.create_entry(
            user=employee,
            date_val=form.cleaned_data["date"],
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data.get("end_time"),
            break_minutes=form.cleaned_data.get("break_minutes", 0),
            project=form.cleaned_data.get("project"),
            notes=form.cleaned_data.get("notes", ""),
            hr_user=request.user,
            http_request=request,
        )
        messages.success(request, "Zeiteintrag erstellt.")
        return redirect("hr:employee_entries", pk=pk)

    return render(
        request,
        "hr/entry_create.html",
        {
            "employee": employee,
            "form": form,
        },
    )


@hr_required
def entry_delete(request, pk, entry_pk):
    """Zeiteintrag löschen (Soft-Delete)."""
    employee = get_object_or_404(User, pk=pk)
    entry = get_object_or_404(TimeEntry, pk=entry_pk, user=employee)
    form = TimeEntryDeleteForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        service = TimeEntryHRService()
        service.soft_delete_entry(
            entry=entry,
            reason=form.cleaned_data["reason"],
            hr_user=request.user,
            http_request=request,
        )
        messages.success(request, "Zeiteintrag gelöscht.")
        return redirect("hr:employee_entries", pk=pk)

    return render(
        request,
        "hr/entry_delete.html",
        {
            "employee": employee,
            "entry": entry,
            "form": form,
        },
    )


@hr_required
def trash(request):
    """Papierkorb: Alle gelöschten Zeiteinträge."""
    deleted_entries = DeletedTimeEntry.objects.order_by("-created_at")
    return render(
        request,
        "hr/trash.html",
        {
            "deleted_entries": deleted_entries,
        },
    )


@hr_required
def restore_entry(request, deleted_pk):
    """Gelöschten Zeiteintrag wiederherstellen."""
    deleted_entry = get_object_or_404(DeletedTimeEntry, pk=deleted_pk)
    service = TimeEntryHRService()
    entry = service.restore_entry(deleted_entry, http_request=request)
    messages.success(request, f"Eintrag vom {entry.date} wiederhergestellt.")
    return redirect("hr:trash")


@hr_required
def adjust_vacation(request, pk):
    """Urlaub manuell korrigieren."""
    employee = get_object_or_404(User, pk=pk)
    form = VacationAdjustmentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        service = AdjustmentService()
        service.adjust_vacation(
            user=employee,
            days=float(form.cleaned_data["days"]),
            reason=form.cleaned_data["reason"],
            hr_user=request.user,
            http_request=request,
        )
        messages.success(
            request, f"Urlaub um {form.cleaned_data['days']} Tage korrigiert."
        )
        return redirect("hr:employee_detail", pk=pk)

    from apps.absences.services import calculate_vacation_entitlement, ApprovalService
    year = timezone.now().year
    entitlement = calculate_vacation_entitlement(employee, year)
    balance = ApprovalService()._get_vacation_balance(employee, year=year)

    return render(
        request,
        "hr/adjust_vacation.html",
        {
            "employee": employee,
            "form": form,
            "current_balance": balance,
            "entitlement": entitlement,
        },
    )


@hr_required
def adjust_overtime(request, pk):
    """Überstunden manuell korrigieren."""
    employee = get_object_or_404(User, pk=pk)
    form = OvertimeAdjustmentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        service = AdjustmentService()
        service.adjust_overtime(
            user=employee,
            minutes=form.cleaned_data["minutes"],
            reason=form.cleaned_data["reason"],
            hr_user=request.user,
            http_request=request,
        )
        messages.success(
            request,
            f"Überstunden um {form.cleaned_data['minutes']} Minuten korrigiert.",
        )
        return redirect("hr:employee_detail", pk=pk)

    calculator = OvertimeCalculator()
    current_balance = calculator.get_balance_minutes(employee)

    return render(
        request,
        "hr/adjust_overtime.html",
        {
            "employee": employee,
            "form": form,
            "current_balance_hours": round(current_balance / 60, 2),
        },
    )


@hr_required
def employee_sollist_partial(request, pk):
    """Soll/Ist-Übersicht als Partial für AJAX."""
    from django.http import JsonResponse

    employee = get_object_or_404(User, pk=pk)
    year = int(request.GET.get("year", timezone.now().year))
    month = int(request.GET.get("month", timezone.now().month))

    calculator = SollIstCalculator()
    data = calculator.calculate_monthly_hours(employee, year, month)
    carry_over = calculator.get_carry_over(employee, year, month)

    total_balance = carry_over + data["balance_minutes"]

    return JsonResponse(
        {
            "soll_hours": round(data["soll_minutes"] / 60, 2),
            "ist_hours": round(data["ist_minutes"] / 60, 2),
            "balance_hours": round(data["balance_minutes"] / 60, 2),
            "carry_over_hours": round(carry_over / 60, 2),
            "total_balance_hours": round(total_balance / 60, 2),
            "holiday_days": data["holiday_days"],
            "absence_days": data["absence_days"],
        }
    )
