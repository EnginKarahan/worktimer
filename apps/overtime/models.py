from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimestampedModel

User = get_user_model()

TRANSACTION_TYPE_CHOICES = [
    ("monthly_settlement", "Monatsabrechnung"),
    ("absence_deduction", "Abwesenheitsabzug"),
    ("overtime_comp_deduction", "Überstundenausgleich-Abzug"),
    ("manual_adjustment", "Manuelle Anpassung"),
    ("year_end_carryover", "Jahresübertrag"),
]


class OvertimeAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="overtime_account")

    class Meta:
        verbose_name = "Überstundenkonto"
        verbose_name_plural = "Überstundenkonten"

    def __str__(self):
        return f"OT-Konto: {self.user}"


class OvertimeTransaction(TimestampedModel):
    account = models.ForeignKey(OvertimeAccount, on_delete=models.CASCADE, related_name="transactions")
    transaction_date = models.DateField()
    amount_minutes = models.IntegerField()
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    reference_absence = models.ForeignKey(
        "absences.AbsenceRequest", null=True, blank=True, on_delete=models.SET_NULL
    )
    reference_month = models.CharField(max_length=7, blank=True)
    reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_ot_transactions"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "transaction_type", "reference_month"],
                condition=models.Q(reference_month__gt=""),
                name="uq_monthly_settlement"
            )
        ]
        verbose_name = "Überstunden-Transaktion"
        verbose_name_plural = "Überstunden-Transaktionen"

    def __str__(self):
        sign = "+" if self.amount_minutes >= 0 else ""
        return f"{self.account.user} {sign}{self.amount_minutes}min ({self.transaction_type})"
