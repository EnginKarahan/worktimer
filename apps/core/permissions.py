from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission

ROLE_PRIORITY = {"ADMIN": 3, "HR": 2, "EMPLOYEE": 1}


def get_active_role(request) -> str:
    """
    Returns the currently active role for the request.
    Session role takes precedence if it is among the user's assigned roles.
    Falls back to the highest assigned role.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return "EMPLOYEE"
    if user.is_superuser:
        return request.session.get("active_role", "ADMIN")
    assigned = set(user.roles.values_list("role", flat=True))
    if not assigned:
        # graceful fallback: read legacy UserProfile.role
        profile = getattr(user, "userprofile", None)
        legacy = getattr(profile, "role", "EMPLOYEE")
        assigned = {legacy}
    session_role = request.session.get("active_role")
    if session_role and session_role in assigned:
        return session_role
    return max(assigned, key=lambda r: ROLE_PRIORITY.get(r, 0))


def get_role(user, request=None) -> str:
    """
    Returns the user's effective role.
    When a request is provided, the session-based active role is used.
    Without a request, the highest assigned role is returned.
    """
    if request is not None:
        return get_active_role(request)
    if not user or not user.is_authenticated:
        return "EMPLOYEE"
    if user.is_superuser:
        return "ADMIN"
    assigned = list(user.roles.values_list("role", flat=True))
    if assigned:
        return max(assigned, key=lambda r: ROLE_PRIORITY.get(r, 0))
    # legacy fallback
    profile = getattr(user, "userprofile", None)
    return getattr(profile, "role", "EMPLOYEE")


def is_hr_or_admin(user, request=None) -> bool:
    return get_role(user, request=request) in ("HR", "ADMIN")


def hr_required(view_func):
    """Decorator: requires HR or ADMIN active role. Redirects employees to dashboard."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if get_active_role(request) not in ("HR", "ADMIN"):
            messages.error(request, "Keine Berechtigung für diesen Bereich.")
            return redirect("timesessions:dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


class IsHROrAdmin(BasePermission):
    """DRF permission class: requires HR or ADMIN active role."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return get_active_role(request._request) in ("HR", "ADMIN")
