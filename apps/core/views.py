from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.core.permissions import get_role


@login_required
def help_manual(request):
    role = get_role(request.user)
    template_map = {
        "ADMIN": "help/admin.html",
        "HR": "help/hr.html",
        "EMPLOYEE": "help/employee.html",
    }
    return render(request, template_map.get(role, "help/employee.html"))
