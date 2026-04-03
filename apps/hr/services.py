from collections import defaultdict
from datetime import date, datetime, timedelta
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from typing import Optional

WEEKDAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

User = get_user_model()


class AdjustmentService:
    """Service for HR to manually adjust vacation and overtime balances."""

    def adjust_vacation(
        self, user: User, days: float, reason: str, hr_user: User, http_request=None
    ):
        """Manually adjust vacation balance for a user."""
        from apps.absences.models import AbsenceRequest, LeaveType

        with transaction.atomic():
            year = date.today().year

            try:
                leave_type = LeaveType.objects.get(code="VACATION_MANUAL_ADJUSTMENT")
            except LeaveType.DoesNotExist:
                leave_type = LeaveType.objects.create(
                    code="VACATION_MANUAL_ADJUSTMENT",
                    name="Urlaub (Manuell korrigiert)",
                    deducts_from_vacation=False,
                )

            start = end = date.today()
            req = AbsenceRequest.objects.create(
                user=user,
                leave_type=leave_type,
                start_date=start,
                end_date=end,
                duration_days=abs(days),
                reason=reason,
                status="APPROVED",
                approved_at=date.today(),
                approval_comment=f"Manuelle Korrektur: {reason}",
            )

            from apps.core.models import AuditLog

            AuditLog.log(
                hr_user,
                "vacation_adjusted",
                req,
                new={"days": days, "reason": reason, "by": str(hr_user)},
                request=http_request,
            )

            return {
                "days": days,
                "reason": reason,
                "by": str(hr_user),
                "absence_request": req,
            }

    def adjust_overtime(
        self, user: User, minutes: int, reason: str, hr_user: User, http_request=None
    ):
        """Manually adjust overtime balance for a user."""
        from apps.overtime.models import OvertimeAccount, OvertimeTransaction
        from apps.core.models import AuditLog

        with transaction.atomic():
            account, _ = OvertimeAccount.objects.get_or_create(user=user)
            tx = OvertimeTransaction.objects.create(
                account=account,
                transaction_type="manual_adjustment",
                amount_minutes=minutes,
                transaction_date=date.today(),
                reason=f"Manuelle Korrektur: {reason}",
                approved_by=hr_user,
            )

            AuditLog.log(
                hr_user,
                "overtime_adjusted",
                tx,
                new={"minutes": minutes, "reason": reason, "by": str(hr_user)},
                request=http_request,
            )

            return {
                "minutes": minutes,
                "reason": reason,
                "by": str(hr_user),
                "transaction": tx,
            }


class TimeEntryHRService:
    """Service for HR to manage time entries."""

    def create_entry(
        self,
        user: User,
        date_val,
        start_time,
        end_time=None,
        break_minutes=0,
        project=None,
        notes: str = "",
        hr_user: Optional[User] = None,
        http_request=None,
    ):
        """Create a new manual time entry for a user."""
        from apps.timesessions.models import TimeEntry
        from apps.core.models import AuditLog

        with transaction.atomic():
            from apps.core.utils.german_law import calculate_required_break
            tz = timezone.get_current_timezone()

            start_dt = timezone.make_aware(datetime.combine(date_val, start_time), tz)
            end_dt = None
            if end_time:
                end_dt = timezone.make_aware(datetime.combine(date_val, end_time), tz)

            # Apply mandatory break if user-entered break is insufficient
            if end_dt:
                gross = int((end_dt - start_dt).total_seconds() / 60)
                required = calculate_required_break(gross)
                if break_minutes < required:
                    break_minutes = required

            entry = TimeEntry.objects.create(
                user=user,
                date=date_val,
                start_time=start_dt,
                end_time=end_dt,
                break_minutes=break_minutes,
                required_break_minutes=break_minutes,
                project=project,
                notes=notes,
                status="MANUAL" if end_dt else "RUNNING",
            )

            if hr_user:
                AuditLog.log(
                    hr_user,
                    "time_entry_created",
                    entry,
                    new={
                        "date": str(date_val),
                        "start": str(start_time),
                        "end": str(end_time) if end_time else None,
                        "break_minutes": break_minutes,
                    },
                    request=http_request,
                )

            return entry

    def soft_delete_entry(self, entry, reason: str, hr_user: User, http_request=None):
        """Soft delete a time entry with reason."""
        from apps.timesessions.models import TimeEntry, DeletedTimeEntry
        from apps.core.models import AuditLog

        with transaction.atomic():
            DeletedTimeEntry.objects.create(
                original_entry=entry.pk,
                deleted_by=hr_user,
                deletion_reason=reason,
                original_user=entry.user,
                original_date=entry.date,
                original_start_time=entry.start_time,
                original_end_time=entry.end_time,
                original_break_minutes=entry.break_minutes,
                original_net_minutes=entry.net_minutes,
                original_project=entry.project,
            )

            entry.delete()

            AuditLog.log(
                hr_user,
                "time_entry_deleted",
                None,
                new={"reason": reason, "by": str(hr_user), "entry_id": entry.pk},
                request=http_request,
            )

            return entry

    def restore_entry(self, deleted_entry, http_request=None):
        """Restore a soft-deleted time entry."""
        from apps.timesessions.models import TimeEntry
        from apps.core.models import AuditLog

        with transaction.atomic():
            entry = TimeEntry.objects.create(
                user=deleted_entry.original_user,
                date=deleted_entry.original_date,
                start_time=deleted_entry.original_start_time,
                end_time=deleted_entry.original_end_time,
                break_minutes=deleted_entry.original_break_minutes,
                project=deleted_entry.original_project,
                status="MANUAL",
            )

            AuditLog.log(
                deleted_entry.deleted_by,
                "time_entry_restored",
                entry,
                new={"restored_from": deleted_entry.pk},
                request=http_request,
            )

            deleted_entry.delete()
            return entry


class SollIstCalculator:
    """Calculate target (Soll) vs actual (Ist) hours for a month."""

    def calculate_monthly_hours(self, user: User, year: int, month: int) -> dict:
        """Calculate Soll/Ist for a specific month.

        For the current month, Soll is only counted up to today (not future days).
        """
        from apps.core.utils.holiday_utils import is_working_day
        from apps.accounts.models import WorkSchedule
        from apps.timesessions.models import TimeEntry
        from apps.absences.models import AbsenceRequest

        federal_state = getattr(
            getattr(user, "userprofile", None), "federal_state", "BY"
        )

        soll_minutes = 0
        holiday_days = 0
        absence_days = 0

        today = date.today()
        last_day = 28
        while True:
            try:
                date(year, month, last_day + 1)
            except ValueError:
                break
            last_day += 1

        # For the current month cap Soll at today; past months use full month
        if year == today.year and month == today.month:
            soll_last_day = today.day
        else:
            soll_last_day = last_day

        absence_dates = set()
        if AbsenceRequest.objects.filter(
            user=user,
            status="APPROVED",
            start_date__year=year,
            start_date__month__lte=month,
            end_date__year=year,
            end_date__month__gte=month,
        ).exists():
            absence_requests = AbsenceRequest.objects.filter(
                user=user,
                status="APPROVED",
                start_date__year=year,
                start_date__month__lte=month,
                end_date__year=year,
                end_date__month__gte=month,
                leave_type__code__in=["VACATION", "SICK", "UNPAID"],
            ).only("start_date", "end_date")
            for req in absence_requests:
                current = req.start_date
                while current <= req.end_date:
                    if current.month == month:
                        absence_dates.add(current)
                    current += timedelta(days=1)
            absence_days = len(absence_dates)

        work_schedules = list(
            WorkSchedule.objects.filter(
                user=user,
                effective_from__year__lte=year,
                effective_from__month__lte=month,
            )
            .filter(
                models.Q(effective_to__isnull=True)
                | models.Q(effective_to__year__gte=year, effective_to__month__gte=month)
            )
            .order_by("effective_from")
        )

        for day in range(1, soll_last_day + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()

            is_holiday = not is_working_day(current_date, federal_state)
            if is_holiday:
                holiday_days += 1
                continue

            if current_date in absence_dates:
                continue

            schedule = None
            for sched in work_schedules:
                if sched.effective_from <= current_date:
                    schedule = sched
                    break

            if schedule:
                soll_minutes += schedule.get_minutes_for_weekday(weekday)
            else:
                soll_minutes += 480

        exclusion_dates = absence_dates.copy()
        holiday_dates = set()
        for day in range(1, last_day + 1):
            current_date = date(year, month, day)
            if not is_working_day(current_date, federal_state):
                holiday_dates.add(current_date)

        total_excluded_dates = exclusion_dates | holiday_dates

        entries_qs = TimeEntry.objects.filter(
            user=user,
            date__year=year,
            date__month=month,
            status__in=["COMPLETED", "AUTO_CLOSED", "MANUAL"],
            end_time__isnull=False,
        )
        if total_excluded_dates:
            entries_qs = entries_qs.exclude(date__in=list(total_excluded_dates))
        ist_minutes = sum(e.net_minutes for e in entries_qs)

        return {
            "soll_minutes": soll_minutes,
            "ist_minutes": ist_minutes,
            "holiday_days": holiday_days,
            "absence_days": absence_days,
            "balance_minutes": ist_minutes - soll_minutes,
        }

    def get_carry_over(self, user: User, year: int, month: int) -> int:
        """Get carry over balance from previous months."""
        from apps.overtime.models import OvertimeAccount, OvertimeTransaction

        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1

        try:
            account = user.overtime_account
            total = (
                OvertimeTransaction.objects.filter(
                    account=account,
                    transaction_date__year=prev_year,
                    transaction_date__month=prev_month,
                ).aggregate(total=models.Sum("amount_minutes"))["total"]
                or 0
            )
            return total
        except OvertimeAccount.DoesNotExist:
            return 0


class VacationBalanceService:
    """Public service to get vacation balance."""

    def get_balance(self, user: User, year: int) -> float:
        """Get current vacation balance for a user for a given year."""
        from apps.absences.models import AbsenceRequest

        entitlement = self.get_entitlement(user, year)

        used_days = (
            AbsenceRequest.objects.filter(
                user=user,
                status="APPROVED",
                start_date__year=year,
                leave_type__deducts_from_vacation=True,
            ).aggregate(total=models.Sum("duration_days"))["total"]
            or 0
        )

        return round(entitlement - used_days, 1)

    def get_entitlement(self, user: User, year: int) -> float:
        """Get vacation entitlement based on work schedule (public method)."""
        from apps.accounts.models import WorkSchedule

        profile = getattr(user, "userprofile", None)
        if profile and profile.annual_leave_days:
            return float(profile.annual_leave_days)

        return 25.0


class TimesheetBuilder:
    """Build a per-day breakdown of a month for HR timesheet view."""

    def build(self, user: User, year: int, month: int) -> dict:
        from apps.core.utils.holiday_utils import get_holidays_for_year
        from apps.absences.models import AbsenceRequest
        from apps.timesessions.models import TimeEntry
        from apps.accounts.models import WorkSchedule

        federal_state = getattr(getattr(user, "userprofile", None), "federal_state", "BY")

        # Last day of month
        last_day = 28
        while True:
            try:
                date(year, month, last_day + 1)
            except ValueError:
                break
            last_day += 1

        month_start = date(year, month, 1)
        month_end = date(year, month, last_day)

        # Holidays map: date → name
        holidays_map = {h[0]: h[1] for h in get_holidays_for_year(year, federal_state)}

        # Absence map: date → AbsenceRequest
        absence_date_map = {}
        for req in AbsenceRequest.objects.filter(
            user=user,
            status="APPROVED",
            start_date__lte=month_end,
            end_date__gte=month_start,
        ).select_related("leave_type"):
            cur = max(req.start_date, month_start)
            while cur <= min(req.end_date, month_end):
                absence_date_map[cur] = req
                cur += timedelta(days=1)

        # Entries map: date → [TimeEntry]
        entries_map = defaultdict(list)
        for entry in TimeEntry.objects.filter(
            user=user, date__year=year, date__month=month
        ).order_by("start_time").select_related("project"):
            entries_map[entry.date].append(entry)

        # Active WorkSchedule
        schedule = (
            WorkSchedule.objects.filter(
                user=user, effective_from__lte=month_end
            )
            .filter(models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=month_start))
            .order_by("-effective_from")
            .first()
        )

        days = []
        total_soll = 0
        total_ist = 0

        for day_num in range(1, last_day + 1):
            d = date(year, month, day_num)
            weekday = d.weekday()
            is_weekend = weekday >= 5
            holiday_name = holidays_map.get(d)
            absence = absence_date_map.get(d)
            entries = entries_map.get(d, [])

            if is_weekend:
                day_type = "weekend"
                soll = 0
            elif holiday_name:
                day_type = "holiday"
                soll = 0
            elif absence:
                lc = absence.leave_type.code if absence.leave_type else ""
                day_type = "sick" if "SICK" in lc else "vacation" if "VACATION" in lc else "absence"
                soll = 0
            else:
                day_type = "work"
                soll = schedule.get_minutes_for_weekday(weekday) if schedule else 480

            ist = sum(e.net_minutes for e in entries)
            total_soll += soll
            total_ist += ist

            days.append({
                "date": d,
                "weekday_name": WEEKDAY_NAMES[weekday],
                "type": day_type,
                "holiday_name": holiday_name,
                "absence": absence,
                "entries": entries,
                "soll_minutes": soll,
                "ist_minutes": ist,
                "balance_minutes": ist - soll,
            })

        return {
            "days": days,
            "total_soll_minutes": total_soll,
            "total_ist_minutes": total_ist,
            "total_balance_minutes": total_ist - total_soll,
        }
