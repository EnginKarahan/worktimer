from django.db import migrations


FREISTELLUNG = {
    "code": "FREISTELLUNG",
    "name": "Freistellung",
    "is_paid": True,
    "requires_approval": True,
    "deducts_from_vacation": False,
    "deducts_from_overtime": False,
}


def seed(apps, schema_editor):
    LeaveType = apps.get_model("absences", "LeaveType")
    LeaveType.objects.get_or_create(code=FREISTELLUNG["code"], defaults=FREISTELLUNG)


def reverse_seed(apps, schema_editor):
    LeaveType = apps.get_model("absences", "LeaveType")
    LeaveType.objects.filter(code=FREISTELLUNG["code"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("absences", "0004_freistellung_and_nachweis"),
    ]

    operations = [
        migrations.RunPython(seed, reverse_seed),
    ]
