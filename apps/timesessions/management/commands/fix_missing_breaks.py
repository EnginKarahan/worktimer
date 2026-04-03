from django.core.management.base import BaseCommand
from apps.timesessions.models import TimeEntry
from apps.core.utils.german_law import calculate_required_break


class Command(BaseCommand):
    help = "Fix existing time entries where mandatory break (§4 ArbZG) was not applied."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        fixed = 0
        skipped = 0

        entries = TimeEntry.objects.filter(
            end_time__isnull=False,
            status__in=["COMPLETED", "AUTO_CLOSED", "MANUAL"],
        ).select_related("user")

        for entry in entries:
            gross = int((entry.end_time - entry.start_time).total_seconds() / 60)
            required = calculate_required_break(gross)
            if entry.break_minutes < required:
                self.stdout.write(
                    f"  {entry.user.get_full_name()} | {entry.date} | "
                    f"gross={gross}min | break={entry.break_minutes}min → {required}min"
                )
                if not dry_run:
                    entry.break_minutes = required
                    entry.required_break_minutes = required
                    entry.save(update_fields=["break_minutes", "required_break_minutes"])
                fixed += 1
            else:
                skipped += 1

        action = "Would fix" if dry_run else "Fixed"
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{action} {fixed} entries. {skipped} already correct."
            )
        )
