from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import OvertimeTransaction
from .services import OvertimeCalculator


@login_required
def overtime_overview(request):
    calc = OvertimeCalculator()
    balance_minutes = calc.get_balance_minutes(request.user)
    transactions = OvertimeTransaction.objects.filter(
        account__user=request.user
    ).order_by("-transaction_date")
    return render(request, "overtime/overview.html", {
        "balance_minutes": balance_minutes,
        "balance_hours": balance_minutes / 60,
        "transactions": transactions,
    })
