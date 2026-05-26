from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("absences", "0003_add_au_and_type_change"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leavetype",
            name="code",
            field=models.CharField(
                choices=[
                    ("VACATION", "Urlaub"),
                    ("SICK", "Krankheit"),
                    ("SPECIAL", "Sonderurlaub"),
                    ("UNPAID", "Unbezahlter Urlaub"),
                    ("HOLIDAY", "Feiertag"),
                    ("OVERTIME_COMP", "Überstundenausgleich"),
                    ("FREISTELLUNG", "Freistellung"),
                ],
                max_length=30,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="absencerequest",
            name="nachweis_vorhanden",
            field=models.BooleanField(default=False, verbose_name="Bescheinigung liegt vor"),
        ),
        migrations.AddField(
            model_name="absencerequest",
            name="nachweis_eingereicht_am",
            field=models.DateField(blank=True, null=True, verbose_name="Bescheinigung eingereicht am"),
        ),
    ]
