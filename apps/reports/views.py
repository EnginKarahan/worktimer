from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.timezone import now
from django_ratelimit.decorators import ratelimit


@login_required
def reports_overview(request):
    today = now()
    return render(request, "reports/overview.html", {
        "current_year": today.year,
        "current_month": today.month,
    })


@login_required
@ratelimit(key="user", rate="10/m", block=True)
def download_pdf(request):
    from .services.pdf_service import generate_monthly_pdf
    year = int(request.GET.get("year", now().year))
    month = int(request.GET.get("month", now().month))
    pdf = generate_monthly_pdf(request.user, year, month)
    filename = f"arbeitszeitnachweis_{year}_{month:02d}_{request.user.username}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
@ratelimit(key="user", rate="10/m", block=True)
def download_excel(request):
    from .services.excel_service import generate_monthly_excel
    year = int(request.GET.get("year", now().year))
    month = int(request.GET.get("month", now().month))
    data = generate_monthly_excel(request.user, year, month)
    filename = f"arbeitszeitnachweis_{year}_{month:02d}_{request.user.username}.xlsx"
    response = HttpResponse(data, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
