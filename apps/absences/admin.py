from django.contrib import admin
from .models import LeaveType, AbsenceRequest


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_paid", "requires_approval"]


@admin.register(AbsenceRequest)
class AbsenceRequestAdmin(admin.ModelAdmin):
    list_display = ["user", "leave_type", "start_date", "end_date", "status", "approver"]
    list_filter = ["status", "leave_type"]
    search_fields = ["user__username"]
    actions = ["approve_selected"]

    def approve_selected(self, request, queryset):
        service = __import__("apps.absences.services", fromlist=["ApprovalService"]).ApprovalService()
        for req in queryset.filter(status="PENDING"):
            service.approve(req, request.user, "Batch-Genehmigung")
    approve_selected.short_description = "Ausgewählte Anträge genehmigen"
