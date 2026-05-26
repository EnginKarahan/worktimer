from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.absences.models import AbsenceRequest, LeaveType
from apps.absences.services import ApprovalService
from apps.accounts.models import UserProfile, WorkSchedule

User = get_user_model()


def _make_user(username="emp", hire_year=2020):
    user = User.objects.create_user(username=username, password="x")
    UserProfile.objects.create(
        user=user,
        weekly_work_hours=40,
        annual_leave_days=30,
        hire_date=date(hire_year, 1, 1),
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


class TestFreistellungLeaveType(TestCase):
    def test_seed_creates_freistellung_type(self):
        lt = LeaveType.objects.get(code="FREISTELLUNG")
        self.assertEqual(lt.name, "Freistellung")
        self.assertTrue(lt.is_paid)
        self.assertTrue(lt.requires_approval)
        self.assertFalse(lt.deducts_from_vacation)
        self.assertFalse(lt.deducts_from_overtime)


class TestFreistellungSubmission(TestCase):
    def test_submit_with_nachweis_fields(self):
        user = _make_user()
        service = ApprovalService()
        req = service.submit_request(
            user=user,
            leave_type_code="FREISTELLUNG",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 2),
            reason="THW-Einsatz",
            nachweis_vorhanden=True,
            nachweis_eingereicht_am=date(2026, 6, 3),
        )
        self.assertEqual(req.leave_type.code, "FREISTELLUNG")
        self.assertTrue(req.nachweis_vorhanden)
        self.assertEqual(req.nachweis_eingereicht_am, date(2026, 6, 3))
        # No manager → auto-approved
        self.assertEqual(req.status, "APPROVED")

    def test_does_not_deduct_vacation(self):
        user = _make_user()
        service = ApprovalService()
        balance_before = service._get_vacation_balance(user, year=2026)
        service.submit_request(
            user=user,
            leave_type_code="FREISTELLUNG",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 5),
            reason="THW",
        )
        balance_after = service._get_vacation_balance(user, year=2026)
        self.assertEqual(balance_before, balance_after)

    def test_backdated_request_allowed(self):
        user = _make_user()
        service = ApprovalService()
        # 5 days in the past
        req = service.submit_request(
            user=user,
            leave_type_code="FREISTELLUNG",
            start_date=date(2026, 5, 18),
            end_date=date(2026, 5, 19),
            reason="Spontaneinsatz",
        )
        self.assertEqual(req.status, "APPROVED")
        self.assertEqual(req.start_date, date(2026, 5, 18))

    def test_nachweis_date_after_end_date_allowed(self):
        user = _make_user()
        service = ApprovalService()
        req = service.submit_request(
            user=user,
            leave_type_code="FREISTELLUNG",
            start_date=date(2026, 5, 4),
            end_date=date(2026, 5, 5),
            nachweis_vorhanden=True,
            nachweis_eingereicht_am=date(2026, 5, 20),
        )
        self.assertEqual(req.nachweis_eingereicht_am, date(2026, 5, 20))
        self.assertGreater(req.nachweis_eingereicht_am, req.end_date)


class TestEnterFreistellungForEmployee(TestCase):
    def test_hr_can_enter_backdated(self):
        hr = _make_user(username="hr")
        emp = _make_user(username="emp")
        service = ApprovalService()
        req = service.enter_freistellung_for_employee(
            hr_user=hr,
            employee=emp,
            start_date=date(2026, 4, 15),
            end_date=date(2026, 4, 16),
            anlass="THW-Heranziehung",
            nachweis_vorhanden=True,
            nachweis_eingereicht_am=date(2026, 5, 2),
        )
        self.assertEqual(req.status, "APPROVED")
        self.assertEqual(req.user, emp)
        self.assertEqual(req.approver, hr)
        self.assertEqual(req.reason, "THW-Heranziehung")
        self.assertTrue(req.nachweis_vorhanden)
