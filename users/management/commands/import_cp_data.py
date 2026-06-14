"""
Management command: import_cp_data

Imports or updates ZIP codes from a CSV file.
- Resumable: loads existing ZIP codes and creates only missing records.
- Uses bulk_create for new records and bulk_update for existing records with real database primary keys.
- Reports progress every REPORT_EVERY rows.
"""

import time
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from unidecode import unidecode
from data.models import ZipCode

REPORT_EVERY  = 5_000
DEFAULT_BATCH = 1_000
UPDATE_FIELDS = [
    'settlement', 'settlement_type', 'municipality',
    'region', 'city', 'country', 'normalized_settlement',
]


class Command(BaseCommand):
    help = 'Imports ZIP codes from CSV with resumable progress'

    def add_arguments(self, parser):
        parser.add_argument('--path', default='media/file_templates/cp.csv')
        parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH, dest='batch_size')

    def handle(self, *args, **options):
        t0 = time.time()
        created, updated, skipped = self.import_or_update_zipcodes(
            options['path'], options['batch_size']
        )
        elapsed = time.time() - t0
        self.stdout.write(self.style.SUCCESS(
            f'\n[ZIP] Completed in {elapsed:.1f}s - '
            f'created: {created:,}, updated: {updated:,}, skipped: {skipped:,}'
        ))

    def import_or_update_zipcodes(self, file_path, batch_size=DEFAULT_BATCH):
        self.stdout.write(f'[ZIP] Reading {file_path} ...')
        df = pd.read_csv(file_path, dtype=str).fillna('')
        total = len(df)
        self.stdout.write(f'[ZIP] {total:,} rows in CSV.')

        # Load existing records as a {zip_code: object_with_pk} dictionary.
        # This gives bulk_update the real primary key for each row.
        self.stdout.write('[ZIP] Loading existing database records...')
        existing = {z.zip_code: z for z in ZipCode.objects.all()}
        self.stdout.write(
            f'[ZIP] {len(existing):,} already in the database, '
            f'{max(0, total - len(existing)):,} pending creation.\n'
        )

        to_create = []
        to_update = []
        skipped   = 0
        processed = 0
        created   = 0
        updated   = 0
        seen      = set()  # Avoid duplicates within the same CSV file.

        for _, row in df.iterrows():
            processed += 1
            zip_code = (
                row.get('d_codigo') or row.get('zip_code') or row.get('code') or ''
            ).strip()

            if not zip_code or zip_code in seen:
                skipped += 1
                self._maybe_report(processed, total)
                continue

            seen.add(zip_code)
            settlement = row.get('d_asenta') or row.get('settlement') or ''
            data = dict(
                settlement            = settlement,
                settlement_type       = row.get('d_tipo_asenta') or row.get('settlement_type') or '',
                municipality          = row.get('D_mnpio') or row.get('municipality') or '',
                region                = row.get('d_estado') or row.get('region') or row.get('state') or '',
                city                  = row.get('d_ciudad') or row.get('city') or '',
                country               = row.get('country') or 'Mexico',
                normalized_settlement = unidecode(settlement).upper(),
            )

            if zip_code in existing:
                # Update the actual object that already has a database primary key.
                obj = existing[zip_code]
                for field, value in data.items():
                    setattr(obj, field, value)
                to_update.append(obj)
            else:
                to_create.append(ZipCode(zip_code=zip_code, **data))

            # Flush creations.
            if len(to_create) >= batch_size:
                with transaction.atomic():
                    ZipCode.objects.bulk_create(to_create, ignore_conflicts=True)
                created += len(to_create)
                to_create = []

            # Flush updates; objects are guaranteed to have primary keys.
            if len(to_update) >= batch_size:
                with transaction.atomic():
                    updated += ZipCode.objects.bulk_update(to_update, UPDATE_FIELDS)
                to_update = []

            self._maybe_report(processed, total)

        # Flush remaining records.
        if to_create:
            with transaction.atomic():
                ZipCode.objects.bulk_create(to_create, ignore_conflicts=True)
            created += len(to_create)

        if to_update:
            with transaction.atomic():
                updated += ZipCode.objects.bulk_update(to_update, UPDATE_FIELDS)

        self._report(processed, total, newline=True)
        return created, updated, skipped

    def _maybe_report(self, processed, total):
        if processed % REPORT_EVERY == 0 or processed == total:
            self._report(processed, total)

    def _report(self, processed, total, newline=False):
        pct    = processed / total * 100 if total else 0
        filled = int(30 * processed / total) if total else 0
        bar    = '█' * filled + '░' * (30 - filled)
        ending = '\n' if newline else '\r'
        self.stdout.write(
            f'  [{bar}] {pct:5.1f}%  {processed:,}/{total:,} rows',
            ending=ending,
        )
        self.stdout.flush()
