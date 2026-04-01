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

    def _calculate_target_minutes(self, user, year: int, month: int) -> int:
        from datetime import timedelta, date as date_cls
        from apps.core.utils.holiday_utils import is_working_day
        from apps.accounts.models import WorkSchedule

        federal_state = getattr(getattr(user, "userprofile", None), "federal_state", "BY")
        total = 0
        d = date_cls(year, month, 1)
        while d.month == month:
            if is_working_day(d, federal_state):
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
