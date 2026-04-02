from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("", views.profile_view, name="profile"),
    path("switch-role/", views.switch_role, name="switch_role"),
]
