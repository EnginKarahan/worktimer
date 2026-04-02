from django.contrib import admin
from .models import Holiday, AuditLog


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ["date", "name", "federal_state"]
    list_filter = ["federal_state"]
    search_fields = ["name"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor", "actor_role", "action", "entity_type", "entity_id"]
    list_filter = ["action", "entity_type", "actor_role"]
    search_fields = ["actor__username", "action"]
    readonly_fields = ["actor", "actor_role", "action", "entity_type", "entity_id", "old_values", "new_values", "ip_address", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_perms(self, request, app_label=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
