from celery import shared_task
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def auto_clock_out_forgotten():
    from .models import TimeEntry
    from apps.core.models import AuditLog
    from django.core.mail import send_mail
    from django.conf import settings

    today = now().date()
    cutoff = now().replace(hour=23, minute=55, second=0, microsecond=0)
    forgotten = TimeEntry.objects.filter(
        status__in=["RUNNING", "PAUSED"],
        start_time__date=today,
    )
    closed = []
    for entry in forgotten:
        entry.end_time = cutoff
        entry.status = "AUTO_CLOSED"
        entry.notes = (entry.notes + "\n" if entry.notes else "") + "Automatisch ausgestempelt (Mitternacht-Job)"
        entry.save()
        AuditLog.log(None, "auto_clock_out", entry)
        closed.append(entry)

    for entry in closed:
        try:
            send_mail(
                subject="Automatisches Ausstempeln",
                message=(
                    f"Hallo {entry.user.get_full_name() or entry.user.username},\n\n"
                    f"Ihr Timer vom {entry.date} wurde um 23:55 Uhr automatisch gestoppt.\n"
                    f"Bitte prüfen Sie Ihren Zeiteintrag und korrigieren Sie ggf. die Daten.\n\n"
                    f"Ihr Arbeitszeit-Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[entry.user.email],
                fail_silently=True,
            )
        except Exception:
            pass

    return f"{len(closed)} Einträge automatisch geschlossen."
