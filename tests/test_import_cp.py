"""
test_import_cp.py — tests the ZIP-code import management command.

Database note:
  ZipCode is in 'enterprise_data' (DataRouter).
  transaction.atomic() inside import_cp_data without using() also touches 'default'
  for the savepoint, so every test declares both databases.
"""
import csv
import os
import pytest
import tempfile
from io import StringIO
from django.core.management import call_command


def make_csv(rows, path):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'd_codigo', 'd_asenta', 'd_tipo_asenta',
            'D_mnpio', 'd_estado', 'd_ciudad', 'country'
        ])
        writer.writeheader()
        writer.writerows(rows)
    return path


SAMPLE_ROWS = [
    {'d_codigo': '06600', 'd_asenta': 'Juarez',     'd_tipo_asenta': 'Neighborhood',
     'D_mnpio': 'Cuauhtemoc', 'd_estado': 'CDMX', 'd_ciudad': 'CDMX', 'country': 'Mexico'},
    {'d_codigo': '06700', 'd_asenta': 'Roma Norte', 'd_tipo_asenta': 'Neighborhood',
     'D_mnpio': 'Cuauhtemoc', 'd_estado': 'CDMX', 'd_ciudad': 'CDMX', 'country': 'Mexico'},
    {'d_codigo': '06800', 'd_asenta': 'Doctores',   'd_tipo_asenta': 'Neighborhood',
     'D_mnpio': 'Cuauhtemoc', 'd_estado': 'CDMX', 'd_ciudad': 'CDMX', 'country': 'Mexico'},
]


# All import tests require both databases:
# - enterprise_data: stores ZipCode
# - default: transaction.atomic() opens savepoints on the default connection too
@pytest.mark.django_db(databases=['default', 'enterprise_data'])
class TestImportCpData:

    def test_imports_new_rows(self, tmp_path):
        from data.models import ZipCode
        path = make_csv(SAMPLE_ROWS, tmp_path / 'cp.csv')
        call_command('import_cp_data', path=str(path), stdout=StringIO())
        assert ZipCode.objects.using('enterprise_data').count() == 3

    def test_does_not_duplicate_on_second_run(self, tmp_path):
        from data.models import ZipCode
        path = make_csv(SAMPLE_ROWS, tmp_path / 'cp.csv')
        call_command('import_cp_data', path=str(path), stdout=StringIO())
        call_command('import_cp_data', path=str(path), stdout=StringIO())
        assert ZipCode.objects.using('enterprise_data').count() == 3

    def test_deduplicates_repeated_zip_codes_in_csv(self, tmp_path):
        from data.models import ZipCode
        rows = SAMPLE_ROWS + [{
            'd_codigo': '06600',  # Duplicate
            'd_asenta': 'Juarez Bis', 'd_tipo_asenta': 'Neighborhood',
            'D_mnpio': 'Cuauhtemoc', 'd_estado': 'CDMX', 'd_ciudad': 'CDMX', 'country': 'Mexico',
        }]
        path = make_csv(rows, tmp_path / 'cp.csv')
        call_command('import_cp_data', path=str(path), stdout=StringIO())
        assert ZipCode.objects.using('enterprise_data').count() == 3

    def test_skips_rows_without_zip_code(self, tmp_path):
        from data.models import ZipCode
        rows = SAMPLE_ROWS + [
            {'d_codigo': '', 'd_asenta': 'No ZIP', 'd_tipo_asenta': '',
             'D_mnpio': '', 'd_estado': '', 'd_ciudad': '', 'country': 'Mexico'},
        ]
        path = make_csv(rows, tmp_path / 'cp.csv')
        out = StringIO()
        call_command('import_cp_data', path=str(path), stdout=out)
        assert ZipCode.objects.using('enterprise_data').count() == 3
        assert 'skipped: 1' in out.getvalue()

    def test_updates_existing_data(self, tmp_path):
        from data.models import ZipCode
        path1 = make_csv(SAMPLE_ROWS, tmp_path / 'cp_v1.csv')
        call_command('import_cp_data', path=str(path1), stdout=StringIO())

        rows_v2 = [{**r, 'd_asenta': r['d_asenta'] + ' (v2)'} for r in SAMPLE_ROWS]
        path2 = make_csv(rows_v2, tmp_path / 'cp_v2.csv')
        call_command('import_cp_data', path=str(path2), stdout=StringIO())

        assert ZipCode.objects.using('enterprise_data').count() == 3
        zc = ZipCode.objects.using('enterprise_data').get(zip_code='06600')
        assert 'v2' in zc.settlement

    def test_completion_message_in_output(self, tmp_path):
        path = make_csv(SAMPLE_ROWS, tmp_path / 'cp.csv')
        out = StringIO()
        call_command('import_cp_data', path=str(path), stdout=out)
        output = out.getvalue()
        assert any(word in output for word in ['Completed', 'created'])


@pytest.mark.django_db(databases=['default', 'enterprise_data'])
class TestImportCpDataIfEmpty:

    def test_warns_when_csv_does_not_exist(self):
        """When no CSV is available, the command must warn without raising an error."""
        import users.management.commands.import_cp_data_if_empty as mod
        original = mod.CANDIDATE_PATHS
        mod.CANDIDATE_PATHS = ['/nonexistent/path/cp.csv']
        try:
            out = StringIO()
            call_command('import_cp_data_if_empty', stdout=out)
            assert 'No ZIP code file was found' in out.getvalue()
        finally:
            mod.CANDIDATE_PATHS = original

    def test_resumes_incomplete_import(self, tmp_path):
        """If the database has fewer records than the CSV, it imports the missing records."""
        from data.models import ZipCode
        # Preload only 1 of 3
        ZipCode.objects.using('enterprise_data').create(
            zip_code='06600', settlement='Juarez',
            normalized_settlement='JUAREZ', municipality='Cuauhtemoc',
            region='CDMX', city='CDMX', country='Mexico',
        )
        assert ZipCode.objects.using('enterprise_data').count() == 1

        path = make_csv(SAMPLE_ROWS, tmp_path / 'cp.csv')
        import users.management.commands.import_cp_data_if_empty as mod
        original = mod.CANDIDATE_PATHS
        mod.CANDIDATE_PATHS = [str(path)]
        try:
            out = StringIO()
            call_command('import_cp_data_if_empty', stdout=out)
            assert ZipCode.objects.using('enterprise_data').count() == 3
            output = out.getvalue()
            assert any(word in output for word in ['missing', 'resuming', 'Completed'])
        finally:
            mod.CANDIDATE_PATHS = original

    def test_does_not_reimport_completed_data(self, tmp_path):
        """When the database has all CSV records, import nothing."""
        from data.models import ZipCode
        for row in SAMPLE_ROWS:
            ZipCode.objects.using('enterprise_data').create(
                zip_code=row['d_codigo'], settlement=row['d_asenta'],
                normalized_settlement=row['d_asenta'].upper(),
                municipality=row['D_mnpio'], region=row['d_estado'],
                city=row['d_ciudad'], country='Mexico',
            )

        path = make_csv(SAMPLE_ROWS, tmp_path / 'cp.csv')
        import users.management.commands.import_cp_data_if_empty as mod
        original = mod.CANDIDATE_PATHS
        mod.CANDIDATE_PATHS = [str(path)]
        try:
            out = StringIO()
            call_command('import_cp_data_if_empty', stdout=out)
            output = out.getvalue()
            assert any(word in output for word in ['complete', 'nothing to do'])
            assert ZipCode.objects.using('enterprise_data').count() == 3
        finally:
            mod.CANDIDATE_PATHS = original
