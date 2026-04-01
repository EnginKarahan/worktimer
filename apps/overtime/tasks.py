import logging
from datetime import timedelta

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def calculate_daily_overtime(user_id: int, date_str: str):
    """Platzhalter — Tages-OT wird bei monatlicher Abrechnung verrechnet."""
    pass


@shared_task
def settle_monthly_overtime():
    """1. des Monats 06:00: Monatliche OT-Abrechnung für alle aktiven Nutzer."""
    from django.contrib.auth import get_user_model
    from django.utils.timezone import now
    from .services import OvertimeCalculator

    User = get_user_model()
    calc = OvertimeCalculator()
    today = now().date()
    last_month = today.replace(day=1) - timedelta(days=1)

    settled = 0
    errors = 0
    for user in User.objects.filter(is_active=True):
        try:
            calc.settle_month(user, last_month.year, last_month.month)
            settled += 1
        except Exception as e:
            errors += 1
            logger.error("settle_monthly_overtime: Fehler bei User %s: %s", user, e)

    logger.info("settle_monthly_overtime: %d abgerechnet, %d Fehler", settled, errors)
    return {"settled": settled, "errors": errors}


@shared_task
def year_end_overtime_carryover():
    """01.01. 05:00: Jahresabschluss – OT-Saldo übertragen oder verfallen lassen."""
    from django.contrib.auth import get_user_model
    from django.utils.timezone import now
    from django.core.mail import send_mail
    from django.conf import settings
    from .models import OvertimeAccount, OvertimeTransaction
    from .services import OvertimeCalculator

    User = get_user_model()
    today = now().date()
    calc = OvertimeCalculator()

    for user in User.objects.filter(is_active=True):
        try:
            balance = calc.get_balance_minutes(user)
            if balance == 0:
                continue
            account, _ = OvertimeAccount.objects.get_or_create(user=user)
            ref = f"{today.year - 1}-carryover"
            OvertimeTransaction.objects.get_or_create(
                account=account,
                transaction_type="year_end_carryover",
                reference_month=ref,
                defaults={
                    "amount_minutes": 0,  # Übertrag: Saldo bleibt (kein Eingriff)
                    "transaction_date": today,
                    "reason": f"Jahresabschluss {today.year - 1}: Saldo {balance} min übertragen",
                },
            )
            if user.email:
                send_mail(
                    subject=f"Überstunden-Jahresabschluss {today.year - 1}",
                    message=(
                        f"Hallo {user.get_full_name() or user.username},\n\n"
                        f"Ihr Überstunden-Saldo zum Jahresende {today.year - 1}: {balance} Minuten ({balance/60:.1f}h).\n"
                        f"Der Saldo wird ins neue Jahr übertragen."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
        except Exception as e:
            logger.error("year_end_overtime_carryover: Fehler bei User %s: %s", user, e)
