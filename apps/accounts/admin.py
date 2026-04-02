from django.contrib import admin
from .models import UserProfile, WorkSchedule


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "employment_type", "weekly_work_hours", "annual_leave_days", "federal_state", "department"]
    search_fields = ["user__username", "user__email", "user__first_name", "user__last_name"]
    list_filter = ["role", "employment_type", "federal_state"]


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ["user", "effective_from", "effective_to", "monday_minutes"]
    list_filter = ["user"]
