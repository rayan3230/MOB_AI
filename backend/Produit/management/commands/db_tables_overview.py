from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Show database tables with row counts and optional sample rows"

    def add_arguments(self, parser):
        parser.add_argument(
            "--contains",
            default="",
            help="Filter tables by substring (case-insensitive)",
        )
        parser.add_argument(
            "--sample",
            type=int,
            default=0,
            help="Show first N rows for each table (default: 0)",
        )

    def handle(self, *args, **options):
        contains = (options.get("contains") or "").lower().strip()
        sample_n = max(0, int(options.get("sample") or 0))

        table_names = sorted(connection.introspection.table_names())
        if contains:
            table_names = [table for table in table_names if contains in table.lower()]

        if not table_names:
            self.stdout.write(self.style.WARNING("No matching tables found."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(table_names)} table(s)."))

        with connection.cursor() as cursor:
            for table in table_names:
                quoted_table = connection.ops.quote_name(table)
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {quoted_table}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"- {table}: {count} row(s)")
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f"- {table}: count failed ({exc})"))
                    continue

                if sample_n > 0 and count > 0:
                    try:
                        cursor.execute(f"SELECT * FROM {quoted_table} LIMIT %s", [sample_n])
                        rows = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]

                        self.stdout.write(f"  columns: {', '.join(columns)}")
                        for idx, row in enumerate(rows, start=1):
                            row_dict = {columns[i]: row[i] for i in range(len(columns))}
                            self.stdout.write(f"  sample[{idx}]: {row_dict}")
                    except Exception as exc:
                        self.stdout.write(self.style.ERROR(f"  sample failed ({exc})"))
