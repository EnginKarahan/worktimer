from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, WorkSchedule, UserRole

User = get_user_model()


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1
    fk_name = "user"


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserRoleInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "employment_type", "weekly_work_hours", "annual_leave_days", "federal_state", "department"]
    search_fields = ["user__username", "user__email", "user__first_name", "user__last_name"]
    list_filter = ["role", "employment_type", "federal_state"]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "role"]
    list_filter = ["role"]
    search_fields = ["user__username", "user__email"]


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ["user", "effective_from", "effective_to", "monday_minutes"]
    list_filter = ["user"]
