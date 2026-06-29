from datetime import date
from django.db import models
from django.db.models import Sum, F
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from .models import OvertimeAccount, OvertimeTransaction

User = get_user_model()


class OvertimeCalculator:
    def get_balance_minutes(self, user) -> int:
        account, _ = OvertimeAccount.objects.get_or_create(user=user)
        return OvertimeTransaction.objects.filter(
            account=account
        ).aggregate(total=Sum("amount_minutes"))["total"] or 0

    def _get_absence_dates(self, user, year: int, month: int) -> set:
        """Tage mit genehmigter, lohnfortgezahlter/unbezahlter Abwesenheit (kein SOLL)."""
        from datetime import timedelta, date as date_cls
        from apps.absences.models import AbsenceRequest

        month_start = date_cls(year, month, 1)
        last_day = 28
        while True:
            try:
                date_cls(year, month, last_day + 1)
            except ValueError:
                break
            last_day += 1
        month_end = date_cls(year, month, last_day)

        absence_dates = set()
        for req in AbsenceRequest.objects.filter(
            user=user,
            status="APPROVED",
            start_date__lte=month_end,
            end_date__gte=month_start,
            leave_type__code__in=["VACATION", "SICK", "UNPAID", "FREISTELLUNG"],
        ).only("start_date", "end_date"):
            cur = max(req.start_date, month_start)
            while cur <= min(req.end_date, month_end):
                absence_dates.add(cur)
                cur += timedelta(days=1)
        return absence_dates

    def _calculate_target_minutes(self, user, year: int, month: int) -> int:
        from datetime import timedelta, date as date_cls
        from apps.core.utils.holiday_utils import is_working_day
        from apps.accounts.models import WorkSchedule

        federal_state = getattr(getattr(user, "userprofile", None), "federal_state", "BY")
        absence_dates = self._get_absence_dates(user, year, month)
        total = 0
        d = date_cls(year, month, 1)
        while d.month == month:
            if is_working_day(d, federal_state) and d not in absence_dates:
                schedule = WorkSchedule.objects.filter(
                    user=user,
                    effective_from__lte=d,
                ).filter(
                    models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=d)
                ).order_by("-effective_from").first()
                if schedule:
                    total += schedule.get_minutes_for_weekday(d.weekday())
                else:
                    total += 480  # fallback: 8h
            d += timedelta(days=1)
        return total

    def settle_month(self, user, year: int, month: int) -> OvertimeTransaction:
        from apps.timesessions.models import TimeEntry
        from django.db.models import ExpressionWrapper, DurationField

        ref = f"{year}-{month:02d}"
        account, _ = OvertimeAccount.objects.get_or_create(user=user)
        soll_minutes = self._calculate_target_minutes(user, year, month)

        entries = TimeEntry.objects.filter(
            user=user,
            date__year=year,
            date__month=month,
            status__in=["COMPLETED", "AUTO_CLOSED", "MANUAL"],
            end_time__isnull=False,
        )
        ist_minutes = sum(e.net_minutes for e in entries)

        tx, _ = OvertimeTransaction.objects.get_or_create(
            account=account,
            transaction_type="monthly_settlement",
            reference_month=ref,
            defaults={
                "amount_minutes": ist_minutes - soll_minutes,
                "transaction_date": date(year, month, 1),
                "reason": f"Monatliche Abrechnung {ref}: IST={ist_minutes}min, SOLL={soll_minutes}min",
            },
        )
        return tx
