import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)


class ClockInView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key="user", rate="30/m", block=True))
    def post(self, request):
        from apps.timesessions.services import TimerService
        from apps.timesessions.exceptions import AlreadyClockedInError
        try:
            entry = TimerService().clock_in(request.user)
            return Response({"id": entry.id, "status": entry.status, "start_time": entry.start_time})
        except AlreadyClockedInError:
            return Response({"error": "Already clocked in"}, status=status.HTTP_409_CONFLICT)


class PauseView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key="user", rate="30/m", block=True))
    def post(self, request):
        from apps.timesessions.services import TimerService
        from apps.timesessions.exceptions import NotClockedInError
        try:
            entry = TimerService().pause(request.user)
            return Response({"id": entry.id, "status": entry.status})
        except NotClockedInError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class ResumeView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key="user", rate="30/m", block=True))
    def post(self, request):
        from apps.timesessions.services import TimerService
        from apps.timesessions.exceptions import NotClockedInError
        try:
            entry = TimerService().resume(request.user)
            return Response({"id": entry.id, "status": entry.status})
        except NotClockedInError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class ClockOutView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key="user", rate="30/m", block=True))
    def post(self, request):
        from apps.timesessions.services import TimerService
        from apps.timesessions.exceptions import NotClockedInError
        try:
            entry = TimerService().clock_out(request.user)
            return Response({"id": entry.id, "status": entry.status, "net_minutes": entry.net_minutes})
        except NotClockedInError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class TimerStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.timesessions.services import TimerService
        entry = TimerService().get_active_entry(request.user)
        if entry:
            return Response({
                "active": True,
                "id": entry.id,
                "status": entry.status,
                "start_time": entry.start_time,
                "elapsed_minutes": entry.gross_minutes,
            })
        return Response({"active": False})


class TimeEntryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.timesessions.models import TimeEntry
        date_filter = request.query_params.get("date")
        qs = TimeEntry.objects.filter(user=request.user).order_by("-date")
        if date_filter:
            qs = qs.filter(date=date_filter)
        data = [
            {
                "id": e.id,
                "date": e.date,
                "start_time": e.start_time,
                "end_time": e.end_time,
                "net_minutes": e.net_minutes,
                "status": e.status,
            }
            for e in qs[:100]
        ]
        return Response(data)


class AbsenceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.absences.models import AbsenceRequest
        qs = AbsenceRequest.objects.filter(user=request.user).select_related("leave_type").order_by("-start_date")
        data = [
            {
                "id": a.id,
                "leave_type": a.leave_type.name,
                "start_date": a.start_date,
                "end_date": a.end_date,
                "status": a.status,
                "duration_days": float(a.duration_days or 0),
            }
            for a in qs[:50]
        ]
        return Response(data)

    def post(self, request):
        from apps.absences.services import ApprovalService
        from apps.absences.exceptions import InsufficientVacationError, InsufficientOvertimeError
        from datetime import date
        try:
            service = ApprovalService()
            req = service.submit_request(
                user=request.user,
                leave_type_code=request.data["leave_type_code"],
                start_date=date.fromisoformat(request.data["start_date"]),
                end_date=date.fromisoformat(request.data["end_date"]),
                reason=request.data.get("reason", ""),
            )
            return Response({"id": req.id, "status": req.status}, status=status.HTTP_201_CREATED)
        except (InsufficientVacationError, InsufficientOvertimeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (KeyError, ValueError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("AbsenceListView.post: unerwarteter Fehler: %s", e)
            return Response({"error": "Interner Serverfehler"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApproveAbsenceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from apps.absences.models import AbsenceRequest
        from apps.absences.services import ApprovalService
        from django.shortcuts import get_object_or_404
        req = get_object_or_404(AbsenceRequest, pk=pk)
        is_manager = (
            hasattr(req.user, "userprofile") and req.user.userprofile.manager == request.user
        )
        if not (request.user.is_staff or is_manager):
            return Response({"error": "Keine Berechtigung"}, status=status.HTTP_403_FORBIDDEN)
        ApprovalService().approve(req, request.user, request.data.get("comment", ""))
        return Response({"status": "approved"}, status=status.HTTP_200_OK)


class RejectAbsenceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from apps.absences.models import AbsenceRequest
        from apps.absences.services import ApprovalService
        from django.shortcuts import get_object_or_404
        req = get_object_or_404(AbsenceRequest, pk=pk)
        is_manager = (
            hasattr(req.user, "userprofile") and req.user.userprofile.manager == request.user
        )
        if not (request.user.is_staff or is_manager):
            return Response({"error": "Keine Berechtigung"}, status=status.HTTP_403_FORBIDDEN)
        ApprovalService().reject(req, request.user, request.data.get("comment", ""))
        return Response({"status": "rejected"}, status=status.HTTP_200_OK)


class OvertimeBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.overtime.services import OvertimeCalculator
        balance = OvertimeCalculator().get_balance_minutes(request.user)
        return Response({
            "balance_minutes": balance,
            "balance_hours": round(balance / 60, 2),
        })


class MonthlyReportView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key="user", rate="10/m", block=True))
    def get(self, request):
        from apps.reports.services.pdf_service import generate_monthly_pdf
        from django.http import HttpResponse
        from django.utils.timezone import now
        year = int(request.query_params.get("year", now().year))
        month = int(request.query_params.get("month", now().month))
        pdf = generate_monthly_pdf(request.user, year, month)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="report_{year}_{month:02d}.pdf"'
        return response
