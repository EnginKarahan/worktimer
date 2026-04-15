from django.db import transaction
from django.utils.timezone import now
from django.db.models import Sum

from apps.core.models import AuditLog
from apps.core.utils.german_law import (
    calculate_required_break,
    check_daily_max,
    collect_all_violations,
)
from .exceptions import CorrectionWindowError
from .models import TimeEntry
from .exceptions import AlreadyClockedInError, NotClockedInError


class TimerService:
    def clock_in(self, user, project_id=None, notes="") -> TimeEntry:
        with transaction.atomic():
            active = TimeEntry.objects.select_for_update().filter(
                user=user, status="RUNNING"
            ).first()
            if active:
                raise AlreadyClockedInError(active)
            entry = TimeEntry.objects.create(
                user=user,
                date=now().date(),
                start_time=now(),
                status="RUNNING",
                project_id=project_id,
                notes=notes,
            )
            AuditLog.log(user, "clock_in", entry)
            return entry

    def pause(self, user) -> TimeEntry:
        with transaction.atomic():
            entry = TimeEntry.objects.select_for_update().filter(
                user=user, status="RUNNING"
            ).first()
            if not entry:
                raise NotClockedInError("Kein laufender Zeiteintrag gefunden.")
            entry.status = "PAUSED"
            entry.pause_started_at = now()
            entry.save()
            AuditLog.log(user, "pause", entry)
            return entry

    def resume(self, user) -> TimeEntry:
        with transaction.atomic():
            entry = TimeEntry.objects.select_for_update().filter(
                user=user, status="PAUSED"
            ).first()
            if not entry:
                raise NotClockedInError("Kein pausierter Zeiteintrag gefunden.")
            if entry.pause_started_at:
                pause_minutes = int((now() - entry.pause_started_at).total_seconds() / 60)
                entry.break_minutes += pause_minutes
            entry.pause_started_at = None
            entry.status = "RUNNING"
            entry.save()
            AuditLog.log(user, "resume", entry)
            return entry

    def clock_out(self, user) -> TimeEntry:
        with transaction.atomic():
            entry = TimeEntry.objects.select_for_update().filter(
                user=user, status__in=["RUNNING", "PAUSED"]
            ).first()
            if not entry:
                raise NotClockedInError("Kein aktiver Zeiteintrag gefunden.")

            # If clocking out while paused, count the current pause duration
            if entry.status == "PAUSED" and entry.pause_started_at:
                pause_minutes = int((now() - entry.pause_started_at).total_seconds() / 60)
                entry.break_minutes += pause_minutes
                entry.pause_started_at = None

            entry.end_time = now()
            gross = entry.gross_minutes

            required = calculate_required_break(gross)
            if entry.break_minutes < required:
                old_break = entry.break_minutes
                entry.break_minutes = required
                entry.required_break_minutes = required
                AuditLog.log(
                    user, "break_auto_corrected", entry,
                    old={"break_minutes": old_break},
                    new={"break_minutes": required},
                )

            violations = collect_all_violations(gross, entry.break_minutes)
            entry.violations_json = [v.as_dict() for v in violations]
            entry.status = "COMPLETED"
            entry.save()

            from apps.overtime.tasks import calculate_daily_overtime
            calculate_daily_overtime.delay(user.id, str(entry.date))

            AuditLog.log(user, "clock_out", entry)
            return entry

    def get_active_entry(self, user) -> TimeEntry | None:
        return TimeEntry.objects.filter(
            user=user, status__in=["RUNNING", "PAUSED"]
        ).first()


class CorrectionService:
    MAX_DAYS_EMPLOYEE = 7
    MAX_DAYS_HR = 90

    def get_max_correction_days(self, actor) -> int | None:
        from apps.core.permissions import get_role
        role = get_role(actor)
        if role == "ADMIN":
            return None  # unbegrenzt
        if role == "HR":
            return self.MAX_DAYS_HR
        return self.MAX_DAYS_EMPLOYEE

    def correct_entry(self, actor, entry: TimeEntry, new_start, new_end, reason: str) -> TimeEntry:
        from django.utils.timezone import now as tz_now

        max_days = self.get_max_correction_days(actor)
        if max_days is not None:
            earliest = (tz_now().date() - __import__("datetime").timedelta(days=max_days))
            if entry.date < earliest:
                raise CorrectionWindowError(
                    f"Korrektur nur bis {max_days} Tage zurück erlaubt."
                )

        with transaction.atomic():
            old_start = entry.start_time
            old_end = entry.end_time

            if not entry.original_start_time:
                entry.original_start_time = old_start
            if not entry.original_end_time:
                entry.original_end_time = old_end

            entry.start_time = new_start
            entry.end_time = new_end
            entry.date = new_start.date()
            entry.is_manual_correction = True
            entry.corrected_by = actor
            entry.correction_reason = reason
            entry.status = "MANUAL"

            # Recalculate mandatory break for the corrected times
            gross = int((new_end - new_start).total_seconds() / 60)
            required = calculate_required_break(gross)
            if entry.break_minutes < required:
                entry.break_minutes = required
                entry.required_break_minutes = required

            entry.save()

            AuditLog.log(
                actor,
                "time_entry_corrected",
                entry,
                old={"start_time": str(old_start), "end_time": str(old_end)},
                new={"start_time": str(new_start), "end_time": str(new_end), "reason": reason},
            )

        return entry

    def create_manual_entry(self, actor, new_start, new_end, reason: str, break_minutes: int = 0) -> TimeEntry:
        from django.utils.timezone import now as tz_now

        max_days = self.get_max_correction_days(actor)
        entry_date = new_start.date()
        if max_days is not None:
            earliest = (tz_now().date() - __import__("datetime").timedelta(days=max_days))
            if entry_date < earliest:
                raise CorrectionWindowError(
                    f"Nachträgliches Eintragen nur bis {max_days} Tage zurück erlaubt."
                )

        gross = int((new_end - new_start).total_seconds() / 60)
        required = calculate_required_break(gross)
        final_break = max(break_minutes, required)

        violations = collect_all_violations(gross, final_break)

        with transaction.atomic():
            entry = TimeEntry.objects.create(
                user=actor,
                date=entry_date,
                start_time=new_start,
                end_time=new_end,
                break_minutes=final_break,
                required_break_minutes=required,
                status="MANUAL",
                is_manual_correction=True,
                corrected_by=actor,
                correction_reason=reason,
                violations_json=[v.as_dict() for v in violations],
            )
            AuditLog.log(
                actor,
                "time_entry_manually_added",
                entry,
                new={"start_time": str(new_start), "end_time": str(new_end), "reason": reason},
            )

        from apps.overtime.tasks import calculate_daily_overtime
        calculate_daily_overtime.delay(actor.id, str(entry_date))

        return entry
