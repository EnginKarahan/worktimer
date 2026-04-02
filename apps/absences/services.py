from datetime import date, timedelta
from django.db import transaction
from django.db.models import Sum
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from apps.core.utils.holiday_utils import is_working_day
from .models import AbsenceRequest, LeaveType
from .exceptions import InsufficientVacationError, InsufficientOvertimeError

User = get_user_model()


def _get_work_days_per_week(user, year: int) -> float:
    """Count days with >0 minutes in the WorkSchedule effective at start of year."""
    from apps.accounts.models import WorkSchedule
    reference = date(year, 1, 1)
    schedule = (
        WorkSchedule.objects
        .filter(user=user, effective_from__lte=reference)
        .order_by("-effective_from")
        .first()
    )
    if schedule is None:
        schedule = WorkSchedule.objects.filter(user=user).order_by("effective_from").first()
    if schedule is None:
        return 5.0
    day_minutes = [
        schedule.monday_minutes, schedule.tuesday_minutes,
        schedule.wednesday_minutes, schedule.thursday_minutes,
        schedule.friday_minutes, schedule.saturday_minutes,
        schedule.sunday_minutes,
    ]
    return float(sum(1 for m in day_minutes if m > 0))


def calculate_vacation_entitlement(user, year: int) -> float:
    """
    Returns vacation days entitled for the given year.

    Applies:
    1. Base: UserProfile.annual_leave_days (contractual 5-day-week basis)
    2. Work-days adjustment: base × actual_days_per_week / 5
    3. Pro-rata for hire year (§5 BUrlG): base × months_from_hire / 12
    4. §4 BUrlG 6-month Wartezeit: entitlement = 0 if wait period not
       satisfied within the year.
    """
    profile = getattr(user, "userprofile", None)
    if profile is None:
        return 0.0

    base = float(profile.annual_leave_days)
    work_days = _get_work_days_per_week(user, year)
    adjusted = base * work_days / 5.0

    hire_date = profile.hire_date
    if hire_date is None or hire_date.year < year:
        return round(adjusted, 1)
    if hire_date.year > year:
        return 0.0

    # Hire year: check §4 Wartezeit (6 calendar months)
    wait_month = hire_date.month + 6
    wait_year = hire_date.year + (wait_month - 1) // 12
    wait_month = ((wait_month - 1) % 12) + 1
    wait_end = date(wait_year, wait_month, 1)

    if wait_end > date(year, 12, 31):
        return 0.0

    # Pro-rata: months from hire month to December
    months_worked = 13 - hire_date.month
    return round(adjusted * months_worked / 12, 1)


class ApprovalService:
    def _calculate_working_days(self, user, start: date, end: date) -> float:
        federal_state = getattr(getattr(user, "userprofile", None), "federal_state", "BY")
        days = 0.0
        current = start
        while current <= end:
            if is_working_day(current, federal_state):
                days += 1
            current += timedelta(days=1)
        return days

    def _get_vacation_balance(self, user, year=None) -> float:
        if year is None:
            year = now().year
        entitlement = calculate_vacation_entitlement(user, year)
        used = float(AbsenceRequest.objects.filter(
            user=user,
            leave_type__code="VACATION",
            status="APPROVED",
            start_date__year=year,
        ).aggregate(total=Sum("duration_days"))["total"] or 0)
        return entitlement - used

    def submit_request(
        self, user, leave_type_code: str, start_date: date, end_date: date, reason: str = ""
    ) -> AbsenceRequest:
        from apps.overtime.services import OvertimeCalculator
        leave_type = LeaveType.objects.get(code=leave_type_code)
        duration = self._calculate_working_days(user, start_date, end_date)

        if leave_type_code == "VACATION":
            balance = self._get_vacation_balance(user)
            if duration > balance:
                raise InsufficientVacationError(available=balance, requested=duration)

        if leave_type_code == "OVERTIME_COMP":
            ot_balance_days = OvertimeCalculator().get_balance_minutes(user) / 480
            if duration > ot_balance_days:
                raise InsufficientOvertimeError(available=ot_balance_days, requested=duration)

        req = AbsenceRequest.objects.create(
            user=user,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration,
            reason=reason,
            status="PENDING",
        )

        if hasattr(user, "userprofile") and user.userprofile.manager:
            from apps.absences.tasks import notify_manager_new_request
            notify_manager_new_request.delay(req.id)
        else:
            self.approve(req, approver=None, comment="Auto-genehmigt (kein Manager zugewiesen)")
        return req

    def approve(self, request: AbsenceRequest, approver, comment: str = "", http_request=None):
        from apps.core.models import AuditLog
        with transaction.atomic():
            request = AbsenceRequest.objects.select_for_update().get(pk=request.pk)
            if request.status != "PENDING":
                return  # Idempotenz: bereits bearbeitet
            request.status = "APPROVED"
            request.approver = approver
            request.approved_at = now()
            request.approval_comment = comment
            request.save()

            if request.leave_type.deducts_from_overtime:
                from apps.overtime.models import OvertimeAccount, OvertimeTransaction
                account, _ = OvertimeAccount.objects.get_or_create(user=request.user)
                OvertimeTransaction.objects.create(
                    account=account,
                    transaction_type="overtime_comp_deduction",
                    amount_minutes=-int(float(request.duration_days or 0) * 480),
                    reference_absence=request,
                    transaction_date=request.start_date,
                    approved_by=approver,
                )
            AuditLog.log(
                approver, "absence_approved", request,
                new={"comment": comment, "approver": str(approver)},
                request=http_request,
            )
            from apps.absences.tasks import notify_user_approved
            notify_user_approved.delay(request.id)

    def reject(self, request: AbsenceRequest, approver, comment: str = "", http_request=None):
        from apps.core.models import AuditLog
        with transaction.atomic():
            request = AbsenceRequest.objects.select_for_update().get(pk=request.pk)
            if request.status != "PENDING":
                return
            request.status = "REJECTED"
            request.approver = approver
            request.approved_at = now()
            request.approval_comment = comment
            request.save()
            AuditLog.log(
                approver, "absence_rejected", request,
                new={"comment": comment, "approver": str(approver)},
                request=http_request,
            )

    def enter_sick_leave_for_employee(self, hr_user, employee, start_date: date, end_date: date):
        """HR enters sick leave directly for an employee (auto-approved)."""
        req = self.submit_request(
            user=employee,
            leave_type_code="SICK",
            start_date=start_date,
            end_date=end_date,
            reason="Von HR erfasst",
        )
        if req.status == "PENDING":
            self.approve(req, approver=hr_user, comment="Von HR direkt erfasst")
        from apps.core.models import AuditLog
        AuditLog.log(
            hr_user, "sick_leave_entered_by_hr", req,
            new={"employee": str(employee), "start": str(start_date), "end": str(end_date)},
        )
        return req
