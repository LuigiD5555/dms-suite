from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Deprecated: occupation-specific catalog was removed from the public generic model.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'The old occupation catalog importer was removed. Use Person.role/department or create a custom catalog extension.'
        ))
