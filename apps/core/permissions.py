from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission


def get_role(user) -> str:
    """Returns the user's role string. Superusers always get ADMIN."""
    if not user or not user.is_authenticated:
        return "EMPLOYEE"
    if user.is_superuser:
        return "ADMIN"
    profile = getattr(user, "userprofile", None)
    return getattr(profile, "role", "EMPLOYEE")


def is_hr_or_admin(user) -> bool:
    return get_role(user) in ("HR", "ADMIN")


def hr_required(view_func):
    """Decorator: requires HR or ADMIN role. Redirects employees to dashboard."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_hr_or_admin(request.user):
            messages.error(request, "Keine Berechtigung für diesen Bereich.")
            return redirect("timesessions:dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


class IsHROrAdmin(BasePermission):
    """DRF permission class: requires HR or ADMIN role."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_hr_or_admin(request.user))
