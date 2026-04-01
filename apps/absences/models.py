from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimestampedModel

User = get_user_model()

LEAVE_CODE_CHOICES = [
    ("VACATION", "Urlaub"),
    ("SICK", "Krankheit"),
    ("SPECIAL", "Sonderurlaub"),
    ("UNPAID", "Unbezahlter Urlaub"),
    ("HOLIDAY", "Feiertag"),
    ("OVERTIME_COMP", "Überstundenausgleich"),
]

ABSENCE_STATUS_CHOICES = [
    ("PENDING", "Ausstehend"),
    ("APPROVED", "Genehmigt"),
    ("REJECTED", "Abgelehnt"),
    ("CANCELLED", "Storniert"),
]


class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, choices=LEAVE_CODE_CHOICES, unique=True)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    deducts_from_vacation = models.BooleanField(default=False)
    deducts_from_overtime = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Abwesenheitstyp"
        verbose_name_plural = "Abwesenheitstypen"

    def __str__(self):
        return self.name


class AbsenceRequest(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="absences")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.DecimalField(max_digits=4, decimal_places=1, null=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ABSENCE_STATUS_CHOICES, default="PENDING")
    approver = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_absences"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_comment = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "status"])]
        verbose_name = "Abwesenheitsantrag"
        verbose_name_plural = "Abwesenheitsanträge"
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_date__lte=models.F("end_date")),
                name="chk_absence_dates"
            )
        ]

    def __str__(self):
        return f"{self.user} – {self.leave_type} ({self.start_date}…{self.end_date})"
