from django.contrib import admin
from .models import OvertimeAccount, OvertimeTransaction


@admin.register(OvertimeAccount)
class OvertimeAccountAdmin(admin.ModelAdmin):
    list_display = ["user"]


@admin.register(OvertimeTransaction)
class OvertimeTransactionAdmin(admin.ModelAdmin):
    list_display = ["account", "transaction_date", "amount_minutes", "transaction_type", "reference_month"]
    list_filter = ["transaction_type"]
