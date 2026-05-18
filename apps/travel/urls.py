from django.urls import path
from . import views

app_name = "travel"

urlpatterns = [
    # Employee
    path("", views.travel_list, name="list"),
    path("new/", views.travel_create, name="create"),
    path("<int:pk>/", views.travel_detail, name="detail"),
    path("<int:pk>/edit/", views.travel_edit, name="edit"),
    path("<int:pk>/submit/", views.travel_submit, name="submit"),
    path("<int:pk>/reopen/", views.travel_reopen, name="reopen"),
    path("<int:pk>/pdf/", views.travel_pdf, name="pdf"),
    path("<int:pk>/receipts/add/", views.travel_receipt_add, name="receipt_add"),
    path("<int:pk>/receipts/<int:receipt_pk>/delete/", views.travel_receipt_delete, name="receipt_delete"),
    # HR
    path("hr/", views.hr_travel_list, name="hr_list"),
    path("hr/settings/", views.hr_travel_settings, name="hr_settings"),
    path("hr/<int:pk>/", views.hr_travel_detail, name="hr_detail"),
    path("hr/<int:pk>/approve/", views.hr_travel_approve, name="hr_approve"),
    path("hr/<int:pk>/reject/", views.hr_travel_reject, name="hr_reject"),
    path("hr/<int:pk>/pdf/", views.hr_travel_pdf, name="hr_pdf"),
    path("hr/<int:pk>/resend/", views.hr_travel_resend, name="hr_resend"),
]
