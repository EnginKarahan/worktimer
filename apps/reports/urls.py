from django.urls import path
from . import views

app_name = "reports"
urlpatterns = [
    path("", views.reports_overview, name="overview"),
    path("pdf/", views.download_pdf, name="pdf"),
    path("excel/", views.download_excel, name="excel"),
]
