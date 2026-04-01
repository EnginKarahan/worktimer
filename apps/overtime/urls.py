from django.urls import path
from . import views

app_name = "overtime"
urlpatterns = [
    path("", views.overtime_overview, name="overview"),
]
