from django.db import transaction
from django.utils.timezone import now
from django.db.models import Sum

from apps.core.models import AuditLog
from apps.core.utils.german_law import (
    calculate_required_break,
    check_daily_max,
    collect_all_violations,
)
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
