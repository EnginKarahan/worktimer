from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("accounts/", include("allauth.urls")),
    path("api/v1/", include("apps.api.v1.urls")),
    path("", include("apps.timesessions.urls")),
    path("absences/", include("apps.absences.urls")),
    path("overtime/", include("apps.overtime.urls")),
    path("reports/", include("apps.reports.urls")),
    path("accounts/profile/", include("apps.accounts.urls")),
    path("hr/", include("apps.hr.urls")),
    path("help/", include("apps.core.urls")),
]
