import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def notify_hr_new_travel_report(report_id):
    from apps.travel.models import TravelExpenseReport
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mail
    from django.conf import settings

    User = get_user_model()
    try:
        report = TravelExpenseReport.objects.select_related("user").get(pk=report_id)
        hr_emails = (
            User.objects.filter(roles__role__in=["HR", "ADMIN"], is_active=True)
            .exclude(email="")
            .values_list("email", flat=True)
            .distinct()
        )
        recipients = list(hr_emails)
        if not recipients:
            return
        send_mail(
            subject=(
                f"Neue Reisekostenabrechnung: "
                f"{report.user.get_full_name()} – {report.title}"
            ),
            message=(
                f"{report.user.get_full_name()} hat eine Reisekostenabrechnung eingereicht.\n"
                f"Zeitraum: {report.departure_datetime.date()} – {report.return_datetime.date()}\n"
                f"Gesamtbetrag: {report.grand_total} €"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception as exc:
        logger.warning("notify_hr_new_travel_report: Fehler für report_id=%s: %s", report_id, exc)


@shared_task
def notify_employee_travel_decision(report_id):
    from apps.travel.models import TravelExpenseReport, REPORT_STATUS_CHOICES
    from django.core.mail import send_mail
    from django.conf import settings

    status_labels = dict(REPORT_STATUS_CHOICES)
    try:
        report = TravelExpenseReport.objects.select_related("user").get(pk=report_id)
        if not report.user.email:
            return
        status_label = status_labels.get(report.status, report.status)
        comment_line = f"\nKommentar: {report.review_comment}" if report.review_comment else ""
        send_mail(
            subject=f"Ihre Reisekostenabrechnung wurde {status_label}",
            message=(
                f"Ihre Reisekostenabrechnung '{report.title}' "
                f"({report.departure_datetime.date()}) wurde {status_label}.{comment_line}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[report.user.email],
            fail_silently=True,
        )
    except Exception as exc:
        logger.warning(
            "notify_employee_travel_decision: Fehler für report_id=%s: %s", report_id, exc
        )
