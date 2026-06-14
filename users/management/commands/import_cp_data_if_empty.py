"""
Management command: import_cp_data_if_empty

Smart, resumable ZIP code import.

Logic:
  - If the CSV does not exist, warn and continue without an error.
  - If the database has at least as many rows as the CSV, skip the completed import.
  - If the database has fewer rows, import only missing ZIP codes.
  - If the database is empty, import everything.

This makes the command safe to run after every restart. If interrupted, it
resumes without importing existing records again.
"""

import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from data.models import ZipCode
import pandas as pd

CANDIDATE_PATHS = [
    'media/file_templates/cp.csv',
    'media/file_templates/cp_data.csv',
    '/seed/cp.csv',
]


class Command(BaseCommand):
    help = 'Imports ZIP codes at startup and resumes interrupted imports'

    def handle(self, *args, **options):
        csv_path = next(
            (p for p in CANDIDATE_PATHS if os.path.isfile(p) and os.path.getsize(p) > 0),
            None,
        )

        if not csv_path:
            self.stdout.write(self.style.WARNING(
                '[ZIP] No ZIP code file was found.\n'
                '      Place the CSV at media/file_templates/cp.csv and run:\n'
                '       docker compose exec app python manage.py import_cp_data'
            ))
            return

        # Count valid CSV rows with a ZIP code.
        self.stdout.write(f'[ZIP] Checking {csv_path} ...')
        df = pd.read_csv(csv_path, dtype=str).fillna('')
        csv_zip_codes = set()
        for _, row in df.iterrows():
            zc = (row.get('d_codigo') or row.get('zip_code') or row.get('code') or '').strip()
            if zc:
                csv_zip_codes.add(zc)

        total_csv = len(csv_zip_codes)
        total_db  = ZipCode.objects.count()

        self.stdout.write(f'[ZIP] CSV: {total_csv:,} unique codes | DB: {total_db:,} records')

        if total_db >= total_csv:
            self.stdout.write(self.style.SUCCESS(
                f'[ZIP] Import complete ({total_db:,}/{total_csv:,}); nothing to do.'
            ))
            return

        missing = total_csv - total_db
        self.stdout.write(self.style.WARNING(
            f'[ZIP] {missing:,} records are missing; '
            f'{"starting a new import" if total_db == 0 else "resuming the interrupted import"}...'
        ))

        call_command('import_cp_data', path=csv_path, stdout=self.stdout)
