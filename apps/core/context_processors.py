from apps.core.permissions import get_role


def user_role(request):
    if request.user.is_authenticated:
        return {"user_role": get_role(request.user)}
    return {"user_role": None}
