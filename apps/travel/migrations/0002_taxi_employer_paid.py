from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("travel", "0001_initial"),
    ]

    operations = [
        # TravelReceipt: Taxi-Kategorie (Choices-Änderung braucht keine DB-Migration,
        # aber wir fügen die neuen Felder hinzu)
        migrations.AddField(
            model_name="travelreceipt",
            name="taxi_reason",
            field=models.TextField(blank=True, verbose_name="Begründung (Taxi)"),
        ),
        migrations.AddField(
            model_name="travelreceipt",
            name="paid_by_employer",
            field=models.BooleanField(default=False, verbose_name="Bereits durch Arbeitgeber bezahlt"),
        ),
        # TravelExpenseReport: neue denormalisierte Summenfelder
        migrations.AddField(
            model_name="travelexpensereport",
            name="employer_paid_total",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=8,
                verbose_name="Durch AG bezahlt (€)",
            ),
        ),
        migrations.AddField(
            model_name="travelexpensereport",
            name="to_reimburse_total",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=8,
                verbose_name="Zu überweisen (€)",
            ),
        ),
        # RECEIPT_CATEGORY_CHOICES Änderung (TAXI hinzugefügt) ist nur Metadaten
        migrations.AlterField(
            model_name="travelreceipt",
            name="category",
            field=models.CharField(
                choices=[
                    ("HOTEL", "Übernachtung"),
                    ("MEAL", "Mahlzeit"),
                    ("FUEL", "Kraftstoff"),
                    ("PARKING", "Parken"),
                    ("TOLL", "Maut"),
                    ("TICKET", "Fahrkarte / Flug"),
                    ("TAXI", "Taxi"),
                    ("OTHER", "Sonstiges"),
                ],
                max_length=20,
                verbose_name="Kategorie",
            ),
        ),
    ]
