from datetime import date, timedelta
from django.db import transaction
from django.db.models import Sum
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from apps.core.utils.holiday_utils import is_working_day
from .models import AbsenceRequest, LeaveType
from .exceptions import InsufficientVacationError, InsufficientOvertimeError

User = get_user_model()


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

    def _get_vacation_balance(self, user) -> float:
        profile = user.userprofile
        annual = float(profile.annual_leave_days)
        used = float(AbsenceRequest.objects.filter(
            user=user,
            leave_type__code="VACATION",
            status="APPROVED",
            start_date__year=now().year,
        ).aggregate(total=Sum("duration_days"))["total"] or 0)
        return annual - used

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
