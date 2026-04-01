from django.urls import path
from . import views

app_name = "absences"
urlpatterns = [
    path("", views.absence_list, name="list"),
    path("new/", views.absence_create, name="create"),
    path("team/", views.team_calendar, name="team_calendar"),
]
