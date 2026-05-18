from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from apps.core.models import TimestampedModel

User = get_user_model()

REPORT_STATUS_CHOICES = [
    ("DRAFT", "Entwurf"),
    ("SUBMITTED", "Eingereicht"),
    ("APPROVED", "Genehmigt"),
    ("REJECTED", "Abgelehnt"),
]

TRANSPORT_TYPE_CHOICES = [
    ("PRIVATE_CAR", "Privat-Pkw"),
    ("COMPANY_CAR", "Dienst-Pkw"),
    ("TRAIN", "Bahn"),
    ("PLANE", "Flugzeug"),
    ("PUBLIC", "ÖPNV"),
    ("OTHER", "Sonstiges"),
]

DAY_TYPE_CHOICES = [
    ("DEPARTURE", "Abreisetag"),
    ("FULL", "Volltag (24h)"),
    ("RETURN", "Rückreisetag"),
    ("SINGLE", "Eintägige Reise"),
]

RECEIPT_CATEGORY_CHOICES = [
    ("HOTEL", "Übernachtung"),
    ("MEAL", "Mahlzeit"),
    ("FUEL", "Kraftstoff"),
    ("PARKING", "Parken"),
    ("TOLL", "Maut"),
    ("TICKET", "Fahrkarte / Flug"),
    ("TAXI", "Taxi"),
    ("OTHER", "Sonstiges"),
]

VAT_RATE_CHOICES = [
    ("0", "0 %"),
    ("7", "7 %"),
    ("19", "19 %"),
]

BOOKING_CLASS_CHOICES = [
    ("1", "1. Klasse"),
    ("2", "2. Klasse"),
    ("E", "Economy"),
    ("B", "Business"),
]

DISCOUNT_CARD_CHOICES = [
    ("", "Keine"),
    ("BC25", "BahnCard 25"),
    ("BC50", "BahnCard 50"),
    ("BC100", "BahnCard 100"),
    ("OTHER", "Sonstige"),
]


def travel_receipt_upload_path(instance, filename):
    return f"travel/receipts/{instance.report.user_id}/{instance.report_id}/{filename}"


class TravelExpenseReport(TimestampedModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="travel_reports"
    )
    title = models.CharField(max_length=200, verbose_name="Titel / Reisezweck")
    destination = models.CharField(max_length=200, verbose_name="Reiseziel")
    departure_datetime = models.DateTimeField(verbose_name="Abfahrt")
    return_datetime = models.DateTimeField(verbose_name="Rückkehr")
    is_domestic = models.BooleanField(default=True, verbose_name="Inland")

    transport_type = models.CharField(
        max_length=20,
        choices=TRANSPORT_TYPE_CHOICES,
        default="PRIVATE_CAR",
        verbose_name="Verkehrsmittel",
    )
    private_car_km = models.DecimalField(
        max_digits=8,
        decimal_places=1,
        default=Decimal("0"),
        verbose_name="Gefahrene km (Privat-Pkw)",
    )
    booking_class = models.CharField(
        max_length=1,
        choices=BOOKING_CLASS_CHOICES,
        blank=True,
        verbose_name="Buchungsklasse",
    )
    discount_card = models.CharField(
        max_length=10,
        choices=DISCOUNT_CARD_CHOICES,
        blank=True,
        verbose_name="Rabattkarte",
    )

    vma_total = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0"), verbose_name="VMA gesamt (€)"
    )
    transport_total = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0"), verbose_name="Fahrtkosten (€)"
    )
    receipts_total = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0"), verbose_name="Belege gesamt (€)"
    )
    employer_paid_total = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0"), verbose_name="Durch AG bezahlt (€)"
    )
    grand_total = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0"), verbose_name="Gesamtbetrag (€)"
    )
    to_reimburse_total = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0"), verbose_name="Zu überweisen (€)"
    )

    status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS_CHOICES,
        default="DRAFT",
        verbose_name="Status",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_travel_reports",
        verbose_name="Prüfer/in",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True, verbose_name="Kommentar HR")
    notes = models.TextField(blank=True, verbose_name="Anmerkungen")

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "submitted_at"]),
        ]
        ordering = ["-departure_datetime"]
        verbose_name = "Reisekostenabrechnung"
        verbose_name_plural = "Reisekostenabrechnungen"
        constraints = [
            models.CheckConstraint(
                check=models.Q(return_datetime__gte=models.F("departure_datetime")),
                name="chk_travel_dates",
            )
        ]

    def __str__(self):
        return f"{self.user} – {self.title} ({self.departure_datetime.date()})"

    @property
    def is_editable(self):
        return self.status == "DRAFT"


class TravelDay(models.Model):
    report = models.ForeignKey(
        TravelExpenseReport, on_delete=models.CASCADE, related_name="days"
    )
    date = models.DateField(verbose_name="Datum")
    day_type = models.CharField(
        max_length=10, choices=DAY_TYPE_CHOICES, verbose_name="Tagestyp"
    )
    breakfast_provided = models.BooleanField(default=False, verbose_name="Frühstück gestellt")
    lunch_provided = models.BooleanField(default=False, verbose_name="Mittagessen gestellt")
    dinner_provided = models.BooleanField(default=False, verbose_name="Abendessen gestellt")
    overnight = models.BooleanField(default=False, verbose_name="Übernachtung")
    overnight_flat_rate = models.BooleanField(
        default=False, verbose_name="Übernachtungspauschale (20 €)"
    )
    vma_base = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0"), verbose_name="VMA Grundbetrag (€)"
    )
    vma_deduction = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0"), verbose_name="Kürzung (€)"
    )
    vma_net = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0"), verbose_name="VMA netto (€)"
    )

    class Meta:
        unique_together = [("report", "date")]
        ordering = ["date"]
        verbose_name = "Reisetag"
        verbose_name_plural = "Reisetage"

    def __str__(self):
        return f"{self.report} – {self.date}"


class TravelReceipt(TimestampedModel):
    report = models.ForeignKey(
        TravelExpenseReport, on_delete=models.CASCADE, related_name="receipts"
    )
    date = models.DateField(verbose_name="Belegdatum")
    gross_amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Bruttobetrag (€)"
    )
    currency = models.CharField(max_length=3, default="EUR", verbose_name="Währung")
    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Betrag in Fremdwährung",
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Wechselkurs",
    )
    vat_rate = models.CharField(
        max_length=2,
        choices=VAT_RATE_CHOICES,
        default="19",
        verbose_name="MwSt.-Satz",
    )
    category = models.CharField(
        max_length=20, choices=RECEIPT_CATEGORY_CHOICES, verbose_name="Kategorie"
    )
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    taxi_reason = models.TextField(
        blank=True, verbose_name="Begründung (Taxi)"
    )
    paid_by_employer = models.BooleanField(
        default=False, verbose_name="Bereits durch Arbeitgeber bezahlt"
    )
    file = models.FileField(
        upload_to=travel_receipt_upload_path,
        null=True,
        blank=True,
        verbose_name="Datei (Beleg)",
    )

    class Meta:
        ordering = ["date"]
        verbose_name = "Beleg"
        verbose_name_plural = "Belege"

    def __str__(self):
        return f"Beleg {self.date}: {self.gross_amount} {self.currency}"

    @property
    def net_amount(self):
        rate = Decimal(self.vat_rate) / Decimal("100")
        return (self.gross_amount / (1 + rate)).quantize(Decimal("0.01"))

    @property
    def vat_amount(self):
        return (self.gross_amount - self.net_amount).quantize(Decimal("0.01"))


class TravelSettings(models.Model):
    accounting_email = models.EmailField(
        verbose_name="Rechnungswesen E-Mail",
        blank=True,
        help_text=(
            "Empfänger für Reisekostenabrechnung mit PDF + Belegen beim Einreichen. "
            "Leer = Env-Variable TRAVEL_ACCOUNTING_EMAIL wird verwendet."
        ),
    )
    hr_notification_email = models.EmailField(
        blank=True,
        verbose_name="HR-Benachrichtigungs-E-Mail",
        help_text="Leer = alle aktiven HR/Admin-Benutzer erhalten die Benachrichtigung.",
    )

    class Meta:
        verbose_name = "Reisekosten-Einstellungen"
        verbose_name_plural = "Reisekosten-Einstellungen"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
