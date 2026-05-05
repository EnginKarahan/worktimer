from django.contrib import admin
from .models import TravelExpenseReport, TravelDay, TravelReceipt


class TravelDayInline(admin.TabularInline):
    model = TravelDay
    extra = 0
    readonly_fields = ["vma_base", "vma_deduction", "vma_net"]


class TravelReceiptInline(admin.TabularInline):
    model = TravelReceipt
    extra = 0
    readonly_fields = ["net_amount", "vat_amount"]


@admin.register(TravelExpenseReport)
class TravelExpenseReportAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "destination", "departure_datetime", "status", "grand_total"]
    list_filter = ["status", "transport_type", "is_domestic"]
    search_fields = ["user__last_name", "user__first_name", "title", "destination"]
    readonly_fields = [
        "vma_total", "transport_total", "receipts_total", "grand_total",
        "submitted_at", "reviewed_at",
    ]
    inlines = [TravelDayInline, TravelReceiptInline]
