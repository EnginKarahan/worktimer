from django.contrib import admin
from .models import Holiday, AuditLog


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ["date", "name", "federal_state"]
    list_filter = ["federal_state"]
    search_fields = ["name"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor", "action", "entity_type", "entity_id"]
    list_filter = ["action", "entity_type"]
    search_fields = ["actor__username", "action"]
    readonly_fields = ["actor", "action", "entity_type", "entity_id", "old_values", "new_values", "ip_address", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
