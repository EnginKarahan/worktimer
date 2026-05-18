from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("travel", "0002_taxi_employer_paid"),
    ]

    operations = [
        migrations.CreateModel(
            name="TravelSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "accounting_email",
                    models.EmailField(
                        blank=True,
                        help_text=(
                            "Empfänger für Reisekostenabrechnung mit PDF + Belegen beim Einreichen. "
                            "Leer = Env-Variable TRAVEL_ACCOUNTING_EMAIL wird verwendet."
                        ),
                        verbose_name="Rechnungswesen E-Mail",
                    ),
                ),
                (
                    "hr_notification_email",
                    models.EmailField(
                        blank=True,
                        help_text="Leer = alle aktiven HR/Admin-Benutzer erhalten die Benachrichtigung.",
                        verbose_name="HR-Benachrichtigungs-E-Mail",
                    ),
                ),
            ],
            options={
                "verbose_name": "Reisekosten-Einstellungen",
                "verbose_name_plural": "Reisekosten-Einstellungen",
            },
        ),
    ]
