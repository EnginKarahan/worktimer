from django.contrib import admin
from .models import TimeEntry


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "start_time", "end_time", "status", "net_minutes"]
    list_filter = ["status", "date"]
    search_fields = ["user__username"]
    readonly_fields = ["violations_json"]
