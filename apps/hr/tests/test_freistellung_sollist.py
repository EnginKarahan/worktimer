from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.absences.models import AbsenceRequest, LeaveType
from apps.accounts.models import UserProfile, WorkSchedule
from apps.hr.services import SollIstCalculator, TimesheetBuilder

User = get_user_model()


def _make_user():
    user = User.objects.create_user(username="emp", password="x")
    UserProfile.objects.create(
        user=user,
        weekly_work_hours=40,
        annual_leave_days=30,
        hire_date=date(2020, 1, 1),
        federal_state="BY",
    )
    WorkSchedule.objects.create(
        user=user,
        monday_minutes=480, tuesday_minutes=480, wednesday_minutes=480,
        thursday_minutes=480, friday_minutes=480,
        saturday_minutes=0, sunday_minutes=0,
        effective_from=date(2020, 1, 1),
    )
    return user


class TestFreistellungReducesSoll(TestCase):
    def test_freistellung_days_skipped_in_soll(self):
        user = _make_user()
        lt = LeaveType.objects.get(code="FREISTELLUNG")
        # Without Freistellung – baseline May 2026 (Mon-Fri = working days)
        calc = SollIstCalculator()
        baseline = calc.calculate_monthly_hours(user, 2026, 5)

        # Mon 2026-05-04 and Tue 2026-05-05 (both working days)
        AbsenceRequest.objects.create(
            user=user,
            leave_type=lt,
            start_date=date(2026, 5, 4),
            end_date=date(2026, 5, 5),
            duration_days=2,
            status="APPROVED",
        )

        with_freistellung = calc.calculate_monthly_hours(user, 2026, 5)
        # 2 days × 8h = 960 minutes lower SOLL
        self.assertEqual(
            baseline["soll_minutes"] - with_freistellung["soll_minutes"],
            960,
        )


class TestSonderurlaubReducesSoll(TestCase):
    def test_special_excluded_from_soll_and_calculators_agree(self):
        user = _make_user()
        lt, _ = LeaveType.objects.get_or_create(
            code="SPECIAL", defaults={"name": "Sonderurlaub"}
        )
        # Mon 2026-05-04 .. Fri 2026-05-08 (5 working days)
        AbsenceRequest.objects.create(
            user=user,
            leave_type=lt,
            start_date=date(2026, 5, 4),
            end_date=date(2026, 5, 8),
            duration_days=5,
            status="APPROVED",
        )
        calc = SollIstCalculator()
        builder = TimesheetBuilder()
        sollist = calc.calculate_monthly_hours(user, 2026, 5)
        timesheet = builder.build(user, 2026, 5)
        # Both calculators must treat Sonderurlaub as a free day (Soll 0)
        self.assertEqual(
            sollist["soll_minutes"], timesheet["total_soll_minutes"]
        )
        day = next(d for d in timesheet["days"] if d["date"] == date(2026, 5, 4))
        self.assertEqual(day["soll_minutes"], 0)


class TestCancelRestoresSoll(TestCase):
    def test_cancel_sick_restores_soll(self):
        user = _make_user()
        lt, _ = LeaveType.objects.get_or_create(
            code="SICK", defaults={"name": "Krankheit"}
        )
        calc = SollIstCalculator()
        baseline = calc.calculate_monthly_hours(user, 2026, 5)["soll_minutes"]

        a = AbsenceRequest.objects.create(
            user=user,
            leave_type=lt,
            start_date=date(2026, 5, 4),
            end_date=date(2026, 5, 4),
            duration_days=1,
            status="APPROVED",
        )
        # Krankheitstag senkt das Soll
        self.assertLess(
            calc.calculate_monthly_hours(user, 2026, 5)["soll_minutes"], baseline
        )

        from apps.absences.services import ApprovalService
        ApprovalService().cancel(a, hr_user=user, reason="war anwesend")
        a.refresh_from_db()
        self.assertEqual(a.status, "CANCELLED")
        # Nach Storno greift das Soll wieder wie ohne Abwesenheit
        self.assertEqual(
            calc.calculate_monthly_hours(user, 2026, 5)["soll_minutes"], baseline
        )


class TestUpdatePeriodShortensAbsence(TestCase):
    def test_shorten_sick_restores_second_day_soll(self):
        user = _make_user()
        lt, _ = LeaveType.objects.get_or_create(
            code="SICK", defaults={"name": "Krankheit"}
        )
        calc = SollIstCalculator()
        baseline = calc.calculate_monthly_hours(user, 2026, 5)["soll_minutes"]

        # 2-tägige Krankmeldung Mo 04. + Di 05.
        a = AbsenceRequest.objects.create(
            user=user,
            leave_type=lt,
            start_date=date(2026, 5, 4),
            end_date=date(2026, 5, 5),
            duration_days=2,
            status="APPROVED",
        )
        two_day_soll = calc.calculate_monthly_hours(user, 2026, 5)["soll_minutes"]
        self.assertEqual(baseline - two_day_soll, 960)  # 2 × 8h

        from apps.absences.services import ApprovalService
        ApprovalService().update_period(
            a, hr_user=user,
            start_date=date(2026, 5, 4), end_date=date(2026, 5, 4),
            reason="nur erster Tag krank",
        )
        a.refresh_from_db()
        self.assertEqual(a.end_date, date(2026, 5, 4))
        self.assertEqual(float(a.duration_days), 1.0)
        # Nur noch ein Tag ohne Soll → Differenz 480 statt 960
        one_day_soll = calc.calculate_monthly_hours(user, 2026, 5)["soll_minutes"]
        self.assertEqual(baseline - one_day_soll, 480)


class TestTimesheetDayType(TestCase):
    def test_freistellung_day_has_own_day_type(self):
        user = _make_user()
        lt = LeaveType.objects.get(code="FREISTELLUNG")
        AbsenceRequest.objects.create(
            user=user,
            leave_type=lt,
            start_date=date(2026, 5, 4),
            end_date=date(2026, 5, 4),
            duration_days=1,
            status="APPROVED",
        )
        builder = TimesheetBuilder()
        result = builder.build(user, 2026, 5)
        day = next(d for d in result["days"] if d["date"] == date(2026, 5, 4))
        self.assertEqual(day["type"], "freistellung")
        self.assertEqual(day["soll_minutes"], 0)
