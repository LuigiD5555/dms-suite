import logging
import os

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class ImportarExportar(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'In progress'),
        (STATUS_DONE, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    archivo_csv = models.FileField(
        upload_to='temporal/imports',
        default=None,
        null=True,
        blank=True,
        verbose_name='CSV file',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    rows_processed = models.PositiveIntegerField(default=0)
    rows_success = models.PositiveIntegerField(default=0)
    rows_error = models.PositiveIntegerField(default=0)
    error_detail = models.JSONField(default=dict, blank=True)
    imported_at = models.DateTimeField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f'Enterprise DMS Import/Export #{self.pk or "new"} - {self.status}'

    def save(self, *args, **kwargs):
        """
        Preserves compatibility with the current admin flow while adding
        traceability. It does not delete the CSV or object after completion,
        allowing failed imports to be audited and retried.
        """
        run_import = kwargs.pop('run_import', True)
        super().save(*args, **kwargs)

        if run_import and self.archivo_csv and not self.imported_at and self.status != self.STATUS_RUNNING:
            self.run_import()

    def run_import(self):
        from imports.csv_importer import CSVImporter

        log = ImportLog.objects.create(
            import_job=self,
            file_name=os.path.basename(self.archivo_csv.name or ''),
            file_path=getattr(self.archivo_csv, 'path', ''),
            status=ImportLog.STATUS_RUNNING,
        )
        ImportarExportar.objects.filter(pk=self.pk).update(status=self.STATUS_RUNNING)

        try:
            importer = CSVImporter(self.archivo_csv.path, import_log=log)
            result = importer.import_data_from_csv()
            final_status = self.STATUS_DONE if result['errors'] == 0 else self.STATUS_FAILED
            log.status = final_status
            log.rows_processed = result['processed']
            log.rows_success = result['success']
            log.rows_error = result['errors']
            log.error_detail = {'rows': result['error_detail']}
            log.finished_at = timezone.now()
            log.save(update_fields=['status', 'rows_processed', 'rows_success', 'rows_error', 'error_detail', 'finished_at'])

            ImportarExportar.objects.filter(pk=self.pk).update(
                status=final_status,
                rows_processed=result['processed'],
                rows_success=result['success'],
                rows_error=result['errors'],
                error_detail={'rows': result['error_detail']},
                imported_at=timezone.now(),
            )
        except Exception as exc:
            logger.exception('Fatal error while importing CSV %s', self.archivo_csv.name)
            log.status = ImportLog.STATUS_FAILED
            log.error_detail = {'fatal': str(exc)}
            log.finished_at = timezone.now()
            log.save(update_fields=['status', 'error_detail', 'finished_at'])
            ImportarExportar.objects.filter(pk=self.pk).update(
                status=self.STATUS_FAILED,
                error_detail={'fatal': str(exc)},
                imported_at=timezone.now(),
            )
            raise

    class Meta:
        verbose_name = 'Import/Export'
        verbose_name_plural = 'Import/Export'


class ImportLog(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'In progress'),
        (STATUS_DONE, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    import_job = models.ForeignKey(ImportarExportar, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True, default='')
    file_path = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    rows_processed = models.PositiveIntegerField(default=0)
    rows_success = models.PositiveIntegerField(default=0)
    rows_error = models.PositiveIntegerField(default=0)
    error_detail = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f'{self.file_name} - {self.status} ({self.rows_success}/{self.rows_processed})'

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Import log'
        verbose_name_plural = 'Import logs'


class ImportRow(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_OK = 'ok'
    STATUS_ERROR = 'error'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_OK, 'OK'),
        (STATUS_ERROR, 'Error'),
    ]

    import_log = models.ForeignKey(ImportLog, on_delete=models.CASCADE, related_name='rows')
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    error_detail = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Row {self.row_number} - {self.status}'

    class Meta:
        unique_together = ('import_log', 'row_number')
        ordering = ['row_number']
        verbose_name = 'Import row'
        verbose_name_plural = 'Import rows'
