import apps.travel.models
from decimal import Decimal
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TravelExpenseReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200, verbose_name="Titel / Reisezweck")),
                ("destination", models.CharField(max_length=200, verbose_name="Reiseziel")),
                ("departure_datetime", models.DateTimeField(verbose_name="Abfahrt")),
                ("return_datetime", models.DateTimeField(verbose_name="Rückkehr")),
                ("is_domestic", models.BooleanField(default=True, verbose_name="Inland")),
                (
                    "transport_type",
                    models.CharField(
                        choices=[
                            ("PRIVATE_CAR", "Privat-Pkw"),
                            ("COMPANY_CAR", "Dienst-Pkw"),
                            ("TRAIN", "Bahn"),
                            ("PLANE", "Flugzeug"),
                            ("PUBLIC", "ÖPNV"),
                            ("OTHER", "Sonstiges"),
                        ],
                        default="PRIVATE_CAR",
                        max_length=20,
                        verbose_name="Verkehrsmittel",
                    ),
                ),
                (
                    "private_car_km",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0"),
                        max_digits=8,
                        verbose_name="Gefahrene km (Privat-Pkw)",
                    ),
                ),
                (
                    "booking_class",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("1", "1. Klasse"),
                            ("2", "2. Klasse"),
                            ("E", "Economy"),
                            ("B", "Business"),
                        ],
                        max_length=1,
                        verbose_name="Buchungsklasse",
                    ),
                ),
                (
                    "discount_card",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("", "Keine"),
                            ("BC25", "BahnCard 25"),
                            ("BC50", "BahnCard 50"),
                            ("BC100", "BahnCard 100"),
                            ("OTHER", "Sonstige"),
                        ],
                        max_length=10,
                        verbose_name="Rabattkarte",
                    ),
                ),
                (
                    "vma_total",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0"), max_digits=8, verbose_name="VMA gesamt (€)"
                    ),
                ),
                (
                    "transport_total",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0"), max_digits=8, verbose_name="Fahrtkosten (€)"
                    ),
                ),
                (
                    "receipts_total",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0"), max_digits=8, verbose_name="Belege gesamt (€)"
                    ),
                ),
                (
                    "grand_total",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0"), max_digits=8, verbose_name="Gesamtbetrag (€)"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Entwurf"),
                            ("SUBMITTED", "Eingereicht"),
                            ("APPROVED", "Genehmigt"),
                            ("REJECTED", "Abgelehnt"),
                        ],
                        default="DRAFT",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_comment", models.TextField(blank=True, verbose_name="Kommentar HR")),
                ("notes", models.TextField(blank=True, verbose_name="Anmerkungen")),
                (
                    "reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_travel_reports",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Prüfer/in",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="travel_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Reisekostenabrechnung",
                "verbose_name_plural": "Reisekostenabrechnungen",
                "ordering": ["-departure_datetime"],
            },
        ),
        migrations.CreateModel(
            name="TravelDay",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Datum")),
                (
                    "day_type",
                    models.CharField(
                        choices=[
                            ("DEPARTURE", "Abreisetag"),
                            ("FULL", "Volltag (24h)"),
                            ("RETURN", "Rückreisetag"),
                            ("SINGLE", "Eintägige Reise"),
                        ],
                        max_length=10,
                        verbose_name="Tagestyp",
                    ),
                ),
                ("breakfast_provided", models.BooleanField(default=False, verbose_name="Frühstück gestellt")),
                ("lunch_provided", models.BooleanField(default=False, verbose_name="Mittagessen gestellt")),
                ("dinner_provided", models.BooleanField(default=False, verbose_name="Abendessen gestellt")),
                ("overnight", models.BooleanField(default=False, verbose_name="Übernachtung")),
                (
                    "overnight_flat_rate",
                    models.BooleanField(default=False, verbose_name="Übernachtungspauschale (20 €)"),
                ),
                (
                    "vma_base",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        max_digits=6,
                        verbose_name="VMA Grundbetrag (€)",
                    ),
                ),
                (
                    "vma_deduction",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0"), max_digits=6, verbose_name="Kürzung (€)"
                    ),
                ),
                (
                    "vma_net",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0"), max_digits=6, verbose_name="VMA netto (€)"
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="days",
                        to="travel.travelexpensereport",
                    ),
                ),
            ],
            options={
                "verbose_name": "Reisetag",
                "verbose_name_plural": "Reisetage",
                "ordering": ["date"],
            },
        ),
        migrations.CreateModel(
            name="TravelReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField(verbose_name="Belegdatum")),
                (
                    "gross_amount",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Bruttobetrag (€)"),
                ),
                ("currency", models.CharField(default="EUR", max_length=3, verbose_name="Währung")),
                (
                    "original_amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=10,
                        null=True,
                        verbose_name="Betrag in Fremdwährung",
                    ),
                ),
                (
                    "exchange_rate",
                    models.DecimalField(
                        blank=True,
                        decimal_places=6,
                        max_digits=10,
                        null=True,
                        verbose_name="Wechselkurs",
                    ),
                ),
                (
                    "vat_rate",
                    models.CharField(
                        choices=[("0", "0 %"), ("7", "7 %"), ("19", "19 %")],
                        default="19",
                        max_length=2,
                        verbose_name="MwSt.-Satz",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("HOTEL", "Übernachtung"),
                            ("MEAL", "Mahlzeit"),
                            ("FUEL", "Kraftstoff"),
                            ("PARKING", "Parken"),
                            ("TOLL", "Maut"),
                            ("TICKET", "Fahrkarte / Flug"),
                            ("OTHER", "Sonstiges"),
                        ],
                        max_length=20,
                        verbose_name="Kategorie",
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="Beschreibung")),
                (
                    "file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=apps.travel.models.travel_receipt_upload_path,
                        verbose_name="Datei (Beleg)",
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="receipts",
                        to="travel.travelexpensereport",
                    ),
                ),
            ],
            options={
                "verbose_name": "Beleg",
                "verbose_name_plural": "Belege",
                "ordering": ["date"],
            },
        ),
        migrations.AddIndex(
            model_name="travelexpensereport",
            index=models.Index(fields=["user", "status"], name="travel_trav_user_id_idx"),
        ),
        migrations.AddIndex(
            model_name="travelexpensereport",
            index=models.Index(fields=["status", "submitted_at"], name="travel_trav_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="travelexpensereport",
            constraint=models.CheckConstraint(
                check=models.Q(return_datetime__gte=models.F("departure_datetime")),
                name="chk_travel_dates",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="travelday",
            unique_together={("report", "date")},
        ),
    ]
