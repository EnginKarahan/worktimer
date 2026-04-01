from django.contrib import admin
from .models import UserProfile, WorkSchedule


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "employment_type", "weekly_work_hours", "annual_leave_days", "federal_state"]
    search_fields = ["user__username", "user__email"]
    list_filter = ["employment_type", "federal_state"]


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ["user", "effective_from", "effective_to", "monday_minutes"]
    list_filter = ["user"]
