from django.test import TestCase
from apps.core.utils.german_law import (
    calculate_required_break,
    check_break_compliance,
    check_daily_max,
    BreakViolation,
)


class TestCalculateRequiredBreak(TestCase):
    """§4 ArbZG Grenzwerte"""

    def test_exactly_360_minutes_no_break(self):
        self.assertEqual(calculate_required_break(360), 0)

    def test_361_minutes_requires_30_min_break(self):
        self.assertEqual(calculate_required_break(361), 30)

    def test_exactly_540_minutes_30_min_break(self):
        self.assertEqual(calculate_required_break(540), 30)

    def test_541_minutes_requires_45_min_break(self):
        self.assertEqual(calculate_required_break(541), 45)

    def test_600_minutes_requires_45_min_break(self):
        self.assertEqual(calculate_required_break(600), 45)

    def test_less_than_360_no_break(self):
        self.assertEqual(calculate_required_break(200), 0)

    def test_zero_minutes_no_break(self):
        self.assertEqual(calculate_required_break(0), 0)


class TestCheckBreakCompliance(TestCase):
    def test_sufficient_break_no_violations(self):
        violations = check_break_compliance(400, 30)
        self.assertEqual(violations, [])

    def test_insufficient_break_returns_violation(self):
        violations = check_break_compliance(400, 0)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].violation_type, "BREAK_INSUFFICIENT")
        self.assertEqual(violations[0].severity, "ERROR")

    def test_exact_minimum_break_passes(self):
        violations = check_break_compliance(541, 45)
        self.assertEqual(violations, [])


class TestCheckDailyMax(TestCase):
    def test_480_minutes_no_violation(self):
        from apps.core.utils.german_law import check_daily_max
        violations = check_daily_max(480)
        self.assertEqual(violations, [])

    def test_481_minutes_warning(self):
        from apps.core.utils.german_law import check_daily_max
        violations = check_daily_max(481)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, "WARNING")

    def test_601_minutes_error(self):
        from apps.core.utils.german_law import check_daily_max
        violations = check_daily_max(601)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].severity, "ERROR")
        self.assertEqual(violations[0].violation_type, "DAILY_MAX_EXCEEDED")
