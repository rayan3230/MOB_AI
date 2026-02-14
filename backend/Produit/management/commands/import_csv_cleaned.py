from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Import cleaned CSV data from folder_data/csv_cleaned into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-dir",
            default="folder_data/csv_cleaned",
            help="Directory containing cleaned CSV files",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Delete existing imported data before import",
        )

    def handle(self, *args, **options):
        csv_dir = options["csv_dir"]
        truncate = options["truncate"]

        self.stdout.write(f"Starting import from: {csv_dir}")
        if truncate:
            self.stdout.write("Truncate enabled: existing data will be cleared before import.")

        call_command(
            "import_csv_export",
            csv_dir=csv_dir,
            truncate=truncate,
        )

        self.stdout.write(self.style.SUCCESS("Cleaned CSV import completed successfully."))
