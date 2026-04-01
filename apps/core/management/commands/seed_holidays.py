from django.core.management.base import BaseCommand
from apps.core.utils.holiday_utils import get_holidays_for_year
from apps.core.models import Holiday


class Command(BaseCommand):
    help = "Befüllt die Holiday-Tabelle mit Feiertagen aus workalendar"

    def add_arguments(self, parser):
        parser.add_argument("--bundesland", default="BY")
        parser.add_argument("--year", type=int, action="append", dest="years")

    def handle(self, *args, **options):
        bundesland = options["bundesland"]
        years = options["years"] or [2024, 2025, 2026]
        count = 0
        for year in years:
            holidays = get_holidays_for_year(year, bundesland)
            for holiday_date, name in holidays:
                _, created = Holiday.objects.get_or_create(
                    date=holiday_date,
                    federal_state=bundesland,
                    defaults={"name": name},
                )
                if created:
                    count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} Feiertage importiert."))
