from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.overtime.models import OvertimeTransaction
from apps.overtime.services import OvertimeCalculator

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Berechnet Überstunden-Monatstransaktionen rückwirkend neu (ab Einstellungsdatum). "
        "Bestehende monthly_settlement-Einträge werden gelöscht und neu erstellt."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            help="Nur diesen Benutzer (Username) neu berechnen",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Nur anzeigen, was berechnet würde – keine DB-Änderungen",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        username_filter = options.get("user")

        qs = User.objects.filter(is_active=True).select_related("userprofile")
        if username_filter:
            qs = qs.filter(username=username_filter)

        today = date.today()
        first_of_this_month = today.replace(day=1)
        calc = OvertimeCalculator()

        for user in qs:
            profile = getattr(user, "userprofile", None)
            hire_date = profile.hire_date if profile else None

            if not hire_date:
                # Fallback: erstes TimeEntry des Users
                from apps.timesessions.models import TimeEntry
                first_entry = TimeEntry.objects.filter(user=user).order_by("date").first()
                if not first_entry:
                    self.stdout.write(f"  {user.username}: keine Einträge, übersprungen")
                    continue
                hire_date = first_entry.date

            start = hire_date.replace(day=1)
            current = start
            months_processed = 0

            while current < first_of_this_month:
                ref = f"{current.year}-{current.month:02d}"
                if dry_run:
                    self.stdout.write(f"  [dry-run] {user.username}: würde {ref} neu berechnen")
                else:
                    OvertimeTransaction.objects.filter(
                        account__user=user,
                        transaction_type="monthly_settlement",
                        reference_month=ref,
                    ).delete()
                    calc.settle_month(user, current.year, current.month)
                months_processed += 1
                # Advance to first day of next month
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  {user.username}: {months_processed} Monate neu berechnet (ab {start})"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Fertig."))
