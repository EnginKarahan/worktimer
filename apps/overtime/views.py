from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from .models import OvertimeTransaction
from .services import OvertimeCalculator


@login_required
def overtime_overview(request):
    from apps.hr.services import SollIstCalculator
    today = timezone.now().date()
    calc = OvertimeCalculator()
    settled_minutes = calc.get_balance_minutes(request.user)
    current_month = SollIstCalculator().calculate_monthly_hours(
        request.user, today.year, today.month
    )
    current_month_minutes = current_month["balance_minutes"]
    balance_minutes = settled_minutes + current_month_minutes
    transactions = OvertimeTransaction.objects.filter(
        account__user=request.user
    ).order_by("-transaction_date")
    return render(request, "overtime/overview.html", {
        "balance_minutes": balance_minutes,
        "balance_hours": balance_minutes / 60,
        "settled_minutes": settled_minutes,
        "current_month_minutes": current_month_minutes,
        "current_month_soll": current_month["soll_minutes"],
        "current_month_ist": current_month["ist_minutes"],
        "current_month_label": today.strftime("%Y-%m"),
        "transactions": transactions,
    })
