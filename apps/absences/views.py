from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import AbsenceRequest, LeaveType
from .services import ApprovalService
from .exceptions import InsufficientVacationError, InsufficientOvertimeError


@login_required
def absence_list(request):
    from apps.absences.services import calculate_vacation_entitlement
    year = int(request.GET.get("year", timezone.now().year))
    absences = AbsenceRequest.objects.filter(user=request.user).order_by("-start_date")
    entitlement = calculate_vacation_entitlement(request.user, year)
    balance = ApprovalService()._get_vacation_balance(request.user, year=year)
    return render(request, "absences/list.html", {
        "absences": absences,
        "vacation_entitlement": entitlement,
        "vacation_balance": balance,
        "year": year,
    })


@login_required
def absence_create(request):
    leave_types = LeaveType.objects.all()
    if request.method == "POST":
        from datetime import date
        service = ApprovalService()
        leave_type_code = request.POST["leave_type_code"]
        nachweis_eingereicht_am = None
        if leave_type_code == "FREISTELLUNG":
            raw = request.POST.get("nachweis_eingereicht_am", "").strip()
            if raw:
                try:
                    nachweis_eingereicht_am = date.fromisoformat(raw)
                except ValueError:
                    nachweis_eingereicht_am = None
        try:
            service.submit_request(
                user=request.user,
                leave_type_code=leave_type_code,
                start_date=date.fromisoformat(request.POST["start_date"]),
                end_date=date.fromisoformat(request.POST["end_date"]),
                reason=request.POST.get("reason", ""),
                nachweis_vorhanden=bool(request.POST.get("nachweis_vorhanden")),
                nachweis_eingereicht_am=nachweis_eingereicht_am,
            )
            messages.success(request, "Antrag eingereicht.")
            return redirect("absences:list")
        except InsufficientVacationError as e:
            messages.error(request, f"Nicht genug Urlaub: {e.available:.1f} Tage verfügbar.")
        except InsufficientOvertimeError as e:
            messages.error(request, f"Nicht genug Überstunden: {e.available:.1f} Tage.")
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "absences/create.html", {"leave_types": leave_types})


@login_required
def absence_edit(request, pk):
    absence = get_object_or_404(AbsenceRequest, pk=pk, user=request.user)
    if absence.status != "PENDING":
        messages.error(request, "Nur ausstehende Anträge können bearbeitet werden.")
        return redirect("absences:list")

    if request.method == "POST":
        from datetime import date
        from .services import ApprovalService
        try:
            start = date.fromisoformat(request.POST["start_date"])
            end = date.fromisoformat(request.POST["end_date"])
            if end < start:
                raise ValueError("Enddatum vor Startdatum.")
            absence.start_date = start
            absence.end_date = end
            absence.reason = request.POST.get("reason", "")
            absence.duration_days = ApprovalService()._calculate_working_days(
                request.user, start, end
            )
            if absence.leave_type.code == "FREISTELLUNG":
                absence.nachweis_vorhanden = bool(request.POST.get("nachweis_vorhanden"))
                raw = request.POST.get("nachweis_eingereicht_am", "").strip()
                absence.nachweis_eingereicht_am = (
                    date.fromisoformat(raw) if raw else None
                )
            absence.save()
            messages.success(request, "Antrag aktualisiert.")
            return redirect("absences:list")
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "absences/edit.html", {"absence": absence})


@login_required
def team_calendar(request):
    absences = AbsenceRequest.objects.filter(
        status="APPROVED"
    ).select_related("user", "leave_type").order_by("start_date")
    return render(request, "absences/team_calendar.html", {"absences": absences})
