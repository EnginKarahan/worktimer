from dataclasses import dataclass
from datetime import datetime


@dataclass
class BreakViolation:
    violation_type: str   # 'BREAK_INSUFFICIENT', 'DAILY_MAX_EXCEEDED', 'REST_PERIOD_VIOLATION'
    message_key: str      # i18n-Key
    severity: str         # 'WARNING', 'ERROR'

    def as_dict(self):
        return {
            "violation_type": self.violation_type,
            "message_key": self.message_key,
            "severity": self.severity,
        }


def calculate_required_break(work_minutes: int) -> int:
    """§4 ArbZG: Mindest-Pausenminuten.
    > 9h (540 min): 45 Minuten
    > 6h (360 min): 30 Minuten
    ≤ 6h: 0 Minuten
    """
    if work_minutes > 540:
        return 45
    elif work_minutes > 360:
        return 30
    return 0


def check_break_compliance(
    work_minutes: int, actual_break_minutes: int
) -> list[BreakViolation]:
    """Prüft ob die tatsächliche Pause den §4 ArbZG-Anforderungen entspricht."""
    required = calculate_required_break(work_minutes)
    if actual_break_minutes < required:
        return [
            BreakViolation(
                "BREAK_INSUFFICIENT",
                "violations.break_insufficient",
                "ERROR",
            )
        ]
    return []


def check_daily_max(net_work_minutes: int) -> list[BreakViolation]:
    """§3 ArbZG: Max 10h (600 min) absolutes Limit, Warnung ab 8h (480 min)."""
    if net_work_minutes > 600:
        return [
            BreakViolation(
                "DAILY_MAX_EXCEEDED",
                "violations.daily_max",
                "ERROR",
            )
        ]
    elif net_work_minutes > 480:
        return [
            BreakViolation(
                "DAILY_STANDARD_EXCEEDED",
                "violations.daily_standard",
                "WARNING",
            )
        ]
    return []


def check_rest_period(
    prev_end: datetime, next_start: datetime
) -> list[BreakViolation]:
    """§5 ArbZG: Mindestens 11h (660 min) Ruhezeit zwischen Arbeitstagen."""
    rest_minutes = (next_start - prev_end).total_seconds() / 60
    if rest_minutes < 660:
        return [
            BreakViolation(
                "REST_PERIOD_VIOLATION",
                "violations.rest_period",
                "WARNING",
            )
        ]
    return []


def collect_all_violations(
    gross_minutes: int,
    break_minutes: int,
    prev_end: datetime | None = None,
    next_start: datetime | None = None,
) -> list[BreakViolation]:
    """Alle §3/§4/§5 ArbZG-Verstöße zusammengefasst."""
    net = gross_minutes - break_minutes
    violations: list[BreakViolation] = []
    violations.extend(check_break_compliance(gross_minutes, break_minutes))
    violations.extend(check_daily_max(net))
    if prev_end and next_start:
        violations.extend(check_rest_period(prev_end, next_start))
    return violations
