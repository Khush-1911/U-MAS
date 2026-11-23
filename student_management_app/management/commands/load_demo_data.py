from django.core.management.base import BaseCommand
from student_management_app.demo_data_loader import load_demo_data

class Command(BaseCommand):
    help = "Loads all demo data into the current database (e.g. Render hosted PostgreSQL or local SQLite)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Custom path to demo data fixture JSON file.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting demo data load...")
        try:
            summary = load_demo_data(options.get("file"))
            self.stdout.write(self.style.SUCCESS("Demo data loaded successfully!"))
            for key, val in summary.items():
                self.stdout.write(f"  - {key}: {val}")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to load demo data: {e}"))
            raise
