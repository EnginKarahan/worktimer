from django.db import migrations

LEAVE_TYPE_DATA = [
    {
        "code": "VACATION",
        "name": "Urlaub",
        "is_paid": True,
        "requires_approval": True,
        "deducts_from_vacation": True,
        "deducts_from_overtime": False,
    },
    {
        "code": "SICK",
        "name": "Krank",
        "is_paid": True,
        "requires_approval": False,
        "deducts_from_vacation": False,
        "deducts_from_overtime": False,
    },
    {
        "code": "SPECIAL",
        "name": "Sonderurlaub",
        "is_paid": True,
        "requires_approval": True,
        "deducts_from_vacation": False,
        "deducts_from_overtime": False,
    },
    {
        "code": "UNPAID",
        "name": "Unbezahlter Urlaub",
        "is_paid": False,
        "requires_approval": True,
        "deducts_from_vacation": False,
        "deducts_from_overtime": False,
    },
    {
        "code": "OVERTIME_COMP",
        "name": "Überstundenausgleich",
        "is_paid": True,
        "requires_approval": True,
        "deducts_from_vacation": False,
        "deducts_from_overtime": True,
    },
]


def seed_leave_types(apps, schema_editor):
    LeaveType = apps.get_model("absences", "LeaveType")
    for data in LEAVE_TYPE_DATA:
        LeaveType.objects.get_or_create(code=data["code"], defaults=data)


def reverse_seed(apps, schema_editor):
    LeaveType = apps.get_model("absences", "LeaveType")
    codes = [d["code"] for d in LEAVE_TYPE_DATA]
    LeaveType.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("absences", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_leave_types, reverse_seed),
    ]
