from apps.core.permissions import get_active_role
from apps.accounts.models import ROLE_CHOICES


def user_role(request):
    if request.user.is_authenticated:
        active = get_active_role(request)
        if request.user.is_superuser:
            assigned = [r[0] for r in ROLE_CHOICES]
        else:
            assigned = list(request.user.roles.values_list("role", flat=True))
            if not assigned:
                profile = getattr(request.user, "userprofile", None)
                legacy = getattr(profile, "role", "EMPLOYEE")
                assigned = [legacy]
        role_labels = dict(ROLE_CHOICES)
        user_roles_display = [(r, role_labels.get(r, r)) for r in assigned]
        return {
            "user_role": active,
            "user_roles": assigned,
            "user_roles_display": user_roles_display,
        }
    return {"user_role": None, "user_roles": [], "user_roles_display": []}
