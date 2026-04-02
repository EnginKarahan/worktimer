from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimestampedModel

User = get_user_model()

STATUS_CHOICES = [
    ("RUNNING", "Läuft"),
    ("PAUSED", "Pausiert"),
    ("COMPLETED", "Abgeschlossen"),
    ("AUTO_CLOSED", "Automatisch geschlossen"),
    ("MANUAL", "Manuell eingetragen"),
]


class TimeEntry(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="time_entries")
    date = models.DateField(db_index=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    break_minutes = models.IntegerField(default=0)
    required_break_minutes = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RUNNING")
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.SET_NULL
    )
    notes = models.TextField(blank=True)
    violations_json = models.JSONField(null=True, blank=True)
    is_manual_correction = models.BooleanField(default=False)
    corrected_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="corrections_made"
    )
    correction_reason = models.TextField(blank=True)
    original_start_time = models.DateTimeField(null=True, blank=True)
    original_end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "date"])]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="RUNNING"),
                name="uq_user_running",
            )
        ]
        verbose_name = "Zeiteintrag"
        verbose_name_plural = "Zeiteinträge"

    def __str__(self):
        return f"{self.user} – {self.date} ({self.status})"

    @property
    def gross_minutes(self) -> int:
        if not self.end_time:
            from django.utils import timezone
            end = timezone.now()
        else:
            end = self.end_time
        return int((end - self.start_time).total_seconds() / 60)

    @property
    def net_minutes(self) -> int:
        return max(0, self.gross_minutes - self.break_minutes)
