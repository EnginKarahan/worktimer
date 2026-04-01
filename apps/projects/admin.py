from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "client", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code", "client"]
