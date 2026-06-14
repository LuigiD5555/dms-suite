from django.contrib import admin
from imports.models import ImportarExportar, ImportLog, ImportRow


@admin.register(ImportarExportar)
class ImportarExportarAdmin(admin.ModelAdmin):
    list_display = ('archivo_csv', 'status', 'rows_processed', 'rows_success', 'rows_error', 'imported_at', 'created_at')
    readonly_fields = ('status', 'rows_processed', 'rows_success', 'rows_error', 'error_detail', 'imported_at', 'created_at')
    list_filter = ('status', 'created_at', 'imported_at')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        latest_log = obj.logs.order_by('-started_at').first()
        if latest_log and latest_log.user_id is None:
            latest_log.user = request.user
            latest_log.save(update_fields=['user'])


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'status', 'rows_processed', 'rows_success', 'rows_error', 'user', 'started_at', 'finished_at')
    readonly_fields = ('import_job', 'user', 'file_name', 'file_path', 'status', 'started_at', 'finished_at', 'rows_processed', 'rows_success', 'rows_error', 'error_detail')
    list_filter = ('status', 'started_at', 'finished_at')
    search_fields = ('file_name',)


@admin.register(ImportRow)
class ImportRowAdmin(admin.ModelAdmin):
    list_display = ('import_log', 'row_number', 'status', 'created_at')
    readonly_fields = ('import_log', 'row_number', 'raw_data', 'status', 'error_detail', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('error_detail',)
