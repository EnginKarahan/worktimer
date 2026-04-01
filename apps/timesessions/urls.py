from django.urls import path
from . import views

app_name = "timesessions"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("timer/", views.timer_view, name="timer"),
    path("timer/status/", views.timer_status, name="timer_status"),
    path("timer/clock-in/", views.clock_in, name="clock_in"),
    path("timer/clock-out/", views.clock_out, name="clock_out"),
    path("timer/pause/", views.pause_view, name="pause"),
    path("timer/resume/", views.resume_view, name="resume"),
    path("entries/", views.entries_list, name="entries"),
]
