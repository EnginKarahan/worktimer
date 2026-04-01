from datetime import date
from io import BytesIO
from django.contrib.auth import get_user_model
from django.conf import settings
from django.template.loader import render_to_string

User = get_user_model()


def generate_monthly_pdf(user, year: int, month: int) -> bytes:
    """Erstellt einen Monatsarbeitszeitbericht als PDF (WeasyPrint)."""
    from apps.timesessions.models import TimeEntry
    from apps.absences.models import AbsenceRequest
    from apps.overtime.services import OvertimeCalculator

    entries = list(
        TimeEntry.objects.filter(
            user=user, date__year=year, date__month=month,
            status__in=["COMPLETED", "AUTO_CLOSED", "MANUAL"],
        ).order_by("date")
    )
    absences = list(
        AbsenceRequest.objects.filter(
            user=user,
            start_date__year=year,
            start_date__month=month,
            status="APPROVED",
        ).select_related("leave_type")
    )

    total_net = sum(e.net_minutes for e in entries)
    ot_balance = OvertimeCalculator().get_balance_minutes(user)

    context = {
        "user": user,
        "year": year,
        "month": month,
        "month_name": date(year, month, 1).strftime("%B %Y"),
        "entries": entries,
        "absences": absences,
        "total_net_minutes": total_net,
        "total_net_hours": total_net / 60,
        "ot_balance_minutes": ot_balance,
        "company_name": getattr(settings, "COMPANY_NAME", "Alhambra"),
        "generated_at": __import__("django.utils.timezone", fromlist=["now"]).now(),
    }

    html = render_to_string("reports/monthly_pdf.html", context)

    from weasyprint import HTML
    pdf = HTML(string=html).write_pdf()
    return pdf
