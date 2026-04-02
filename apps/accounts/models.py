from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimestampedModel

User = get_user_model()

EMPLOYMENT_TYPES = [
    ("FULL_TIME", "Vollzeit"),
    ("PART_TIME", "Teilzeit"),
    ("MINI_JOB", "Minijob"),
    ("INTERN", "Praktikant"),
]

ROLE_CHOICES = [
    ("EMPLOYEE", "Mitarbeiter"),
    ("HR", "Personalmanagement"),
    ("ADMIN", "Admin"),
]

FEDERAL_STATES = [
    ("BW", "Baden-Württemberg"), ("BY", "Bayern"), ("BE", "Berlin"),
    ("BB", "Brandenburg"), ("HB", "Bremen"), ("HH", "Hamburg"),
    ("HE", "Hessen"), ("MV", "Mecklenburg-Vorpommern"), ("NI", "Niedersachsen"),
    ("NW", "Nordrhein-Westfalen"), ("RP", "Rheinland-Pfalz"), ("SL", "Saarland"),
    ("SN", "Sachsen"), ("ST", "Sachsen-Anhalt"), ("SH", "Schleswig-Holstein"),
    ("TH", "Thüringen"),
]


class UserProfile(TimestampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    weekly_work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=40.0)
    annual_leave_days = models.IntegerField(default=30)
    hire_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default="FULL_TIME")
    manager = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports"
    )
    federal_state = models.CharField(max_length=2, choices=FEDERAL_STATES, default="BY")
    leave_carry_over = models.BooleanField(default=True)
    max_carry_over_days = models.DecimalField(max_digits=4, decimal_places=1, default=5.0)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="EMPLOYEE", verbose_name="Rolle")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Telefon")
    department = models.CharField(max_length=100, blank=True, verbose_name="Abteilung")

    class Meta:
        verbose_name = "Mitarbeiterprofil"
        verbose_name_plural = "Mitarbeiterprofile"

    def __str__(self):
        return f"Profil: {self.user.get_full_name() or self.user.username}"

    @property
    def daily_work_minutes(self) -> int:
        return int(self.weekly_work_hours * 60 / 5)


class WorkSchedule(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="work_schedules")
    monday_minutes = models.IntegerField(default=480)
    tuesday_minutes = models.IntegerField(default=480)
    wednesday_minutes = models.IntegerField(default=480)
    thursday_minutes = models.IntegerField(default=480)
    friday_minutes = models.IntegerField(default=480)
    saturday_minutes = models.IntegerField(default=0)
    sunday_minutes = models.IntegerField(default=0)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "effective_from"])]
        ordering = ["-effective_from"]
        verbose_name = "Arbeitszeitplan"
        verbose_name_plural = "Arbeitszeitpläne"

    def get_minutes_for_weekday(self, weekday: int) -> int:
        days = [
            self.monday_minutes, self.tuesday_minutes, self.wednesday_minutes,
            self.thursday_minutes, self.friday_minutes, self.saturday_minutes,
            self.sunday_minutes,
        ]
        return days[weekday]
