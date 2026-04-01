import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def notify_manager_new_request(request_id: int):
    from .models import AbsenceRequest
    try:
        req = AbsenceRequest.objects.select_related("user", "user__userprofile__manager").get(pk=request_id)
        manager = req.user.userprofile.manager
        if not manager or not manager.email:
            return
        send_mail(
            subject=f"Neuer Abwesenheitsantrag von {req.user.get_full_name()}",
            message=f"{req.user.get_full_name()} beantragt {req.leave_type.name} vom {req.start_date} bis {req.end_date}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[manager.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.warning("notify_manager_new_request: Fehler für request_id=%s: %s", request_id, e)


@shared_task
def notify_user_approved(request_id: int):
    from .models import AbsenceRequest
    try:
        req = AbsenceRequest.objects.select_related("user").get(pk=request_id)
        if not req.user.email:
            return
        send_mail(
            subject=f"Ihr Antrag wurde {req.get_status_display()}",
            message=f"Ihr Abwesenheitsantrag ({req.leave_type.name}, {req.start_date}–{req.end_date}) wurde {req.get_status_display()}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[req.user.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.warning("notify_user_approved: Fehler für request_id=%s: %s", request_id, e)


@shared_task
def check_medical_cert_required():
    """Täglich 08:00: Warnung an Manager wenn Krankmeldung >= 4 Tage ohne AU-Schein."""
    from datetime import timedelta
    from django.utils.timezone import now
    from .models import AbsenceRequest

    today = now().date()
    threshold = today - timedelta(days=3)  # Beginn war vor 4 Tagen oder früher

    long_sick = AbsenceRequest.objects.filter(
        leave_type__code="SICK",
        status="APPROVED",
        start_date__lte=threshold,
        end_date__gte=today,
    ).select_related("user", "user__userprofile__manager", "leave_type")

    for req in long_sick:
        duration = (today - req.start_date).days + 1
        if duration < 4:
            continue
        manager = getattr(getattr(req.user, "userprofile", None), "manager", None)
        recipients = [r for r in [
            req.user.email if req.user.email else None,
            manager.email if manager and manager.email else None,
        ] if r]
        if not recipients:
            continue
        try:
            send_mail(
                subject=f"Krankmeldung: AU-Bescheinigung erforderlich für {req.user.get_full_name()}",
                message=(
                    f"Hinweis: {req.user.get_full_name()} ist seit {req.start_date} krank ({duration} Tage).\n"
                    f"Ab dem 4. Kranktag ist eine ärztliche Arbeitsunfähigkeitsbescheinigung einzureichen."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True,
            )
        except Exception as e:
            logger.warning("check_medical_cert_required: E-Mail-Fehler für %s: %s", req.user, e)


@shared_task
def vacation_expiry_warning():
    """01.02. jedes Jahr: Warnung bei drohendem Resturlaub-Verfall."""
    from django.utils.timezone import now
    from django.db.models import Sum
    from django.contrib.auth import get_user_model

    User = get_user_model()
    year = now().year - 1  # Prüfe Vorjahr

    for user in User.objects.filter(is_active=True):
        profile = getattr(user, "userprofile", None)
        if not profile or not user.email:
            continue
        annual = float(profile.annual_leave_days)
        used = float(AbsenceRequest.objects.filter(
            user=user,
            leave_type__code="VACATION",
            status="APPROVED",
            start_date__year=year,
        ).aggregate(total=Sum("duration_days"))["total"] or 0)
        remaining = annual - used
        if remaining <= 0:
            continue
        carryover = float(profile.max_carry_over_days)
        expiring = max(0, remaining - carryover)
        try:
            send_mail(
                subject=f"Resturlaub {year}: {remaining:.1f} Tage – Verfall droht",
                message=(
                    f"Hallo {user.get_full_name() or user.username},\n\n"
                    f"Sie haben aus {year} noch {remaining:.1f} Urlaubstage übrig.\n"
                    f"Davon können {carryover:.1f} Tage ins neue Jahr übertragen werden.\n"
                    f"{'⚠️  ' + str(expiring) + ' Tage verfallen, sofern nicht bis 31.03. genommen.' if expiring > 0 else 'Kein Verfall – alle Tage können übertragen werden.'}\n\n"
                    f"Bitte sprechen Sie mit Ihrer Führungskraft."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning("vacation_expiry_warning: E-Mail-Fehler für %s: %s", user, e)
