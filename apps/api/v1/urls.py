from django.urls import path
from . import views

urlpatterns = [
    # Timer
    path("timer/clock-in/", views.ClockInView.as_view(), name="api_clock_in"),
    path("timer/pause/", views.PauseView.as_view(), name="api_pause"),
    path("timer/resume/", views.ResumeView.as_view(), name="api_resume"),
    path("timer/clock-out/", views.ClockOutView.as_view(), name="api_clock_out"),
    path("timer/status/", views.TimerStatusView.as_view(), name="api_timer_status"),
    # Time Entries
    path("time-entries/", views.TimeEntryListView.as_view(), name="api_time_entries"),
    # Absences
    path("absences/", views.AbsenceListView.as_view(), name="api_absences"),
    path("absences/<int:pk>/approve/", views.ApproveAbsenceView.as_view(), name="api_approve_absence"),
    path("absences/<int:pk>/reject/", views.RejectAbsenceView.as_view(), name="api_reject_absence"),
    # Overtime
    path("overtime/balance/", views.OvertimeBalanceView.as_view(), name="api_overtime_balance"),
    # Reports
    path("reports/monthly/", views.MonthlyReportView.as_view(), name="api_monthly_report"),
]
