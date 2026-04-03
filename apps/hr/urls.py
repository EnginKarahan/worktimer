from django.urls import path
from . import views

app_name = "hr"

urlpatterns = [
    path("", views.hr_dashboard, name="dashboard"),
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/new/", views.employee_create, name="employee_create"),
    path("employees/<int:pk>/", views.employee_detail, name="employee_detail"),
    path("employees/<int:pk>/edit/", views.employee_edit, name="employee_edit"),
    path("employees/<int:pk>/delete/", views.employee_delete, name="employee_delete"),
    path(
        "employees/<int:pk>/entries/", views.employee_entries, name="employee_entries"
    ),
    path("employees/<int:pk>/entries/new/", views.entry_create, name="entry_create"),
    path(
        "employees/<int:pk>/entries/<int:entry_pk>/delete/",
        views.entry_delete,
        name="entry_delete",
    ),
    path(
        "employees/<int:pk>/entries/<int:entry_pk>/correct/",
        views.employee_correct_entry,
        name="employee_correct_entry",
    ),
    path(
        "employees/<int:pk>/schedule/",
        views.employee_schedule,
        name="employee_schedule",
    ),
    path(
        "employees/<int:pk>/vacation/adjust/",
        views.adjust_vacation,
        name="adjust_vacation",
    ),
    path(
        "employees/<int:pk>/overtime/adjust/",
        views.adjust_overtime,
        name="adjust_overtime",
    ),
    path(
        "employees/<int:pk>/absences/",
        views.employee_absences,
        name="employee_absences",
    ),
    path("employees/<int:pk>/sick/", views.enter_sick_leave, name="enter_sick_leave"),
    path(
        "employees/<int:pk>/sollist/",
        views.employee_sollist_partial,
        name="employee_sollist_partial",
    ),
    path("trash/", views.trash, name="trash"),
    path("trash/<int:deleted_pk>/restore/", views.restore_entry, name="restore_entry"),
    path("absences/pending/", views.pending_approvals, name="pending_approvals"),
    path("absences/<int:pk>/approve/", views.approve_absence, name="approve_absence"),
    path("absences/<int:pk>/reject/", views.reject_absence, name="reject_absence"),
    path(
        "reports/<int:user_pk>/pdf/", views.download_employee_pdf, name="employee_pdf"
    ),
    path(
        "reports/<int:user_pk>/excel/",
        views.download_employee_excel,
        name="employee_excel",
    ),
]
