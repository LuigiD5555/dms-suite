# Generated manually for Enterprise DMS import audit.

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('imports', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='importarexportar',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('running', 'In progress'), ('done', 'Completed'), ('failed', 'Failed')], db_index=True, default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='importarexportar',
            name='rows_processed',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='importarexportar',
            name='rows_success',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='importarexportar',
            name='rows_error',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='importarexportar',
            name='error_detail',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='importarexportar',
            name='imported_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='importarexportar',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='importarexportar',
            name='archivo_csv',
            field=models.FileField(blank=True, default=None, null=True, upload_to='temporal/imports', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['csv'])]),
        ),
        migrations.CreateModel(
            name='ImportLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(blank=True, default='', max_length=255)),
                ('file_path', models.CharField(blank=True, default='', max_length=500)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'In progress'), ('done', 'Completed'), ('failed', 'Failed')], db_index=True, default='pending', max_length=20)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('rows_processed', models.PositiveIntegerField(default=0)),
                ('rows_success', models.PositiveIntegerField(default=0)),
                ('rows_error', models.PositiveIntegerField(default=0)),
                ('error_detail', models.JSONField(blank=True, default=dict)),
                ('import_job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='imports.importarexportar')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Import log',
                'verbose_name_plural': 'Import logs',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='ImportRow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row_number', models.PositiveIntegerField()),
                ('raw_data', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('ok', 'OK'), ('error', 'Error')], db_index=True, default='pending', max_length=20)),
                ('error_detail', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('import_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rows', to='imports.importlog')),
            ],
            options={
                'verbose_name': 'Import row',
                'verbose_name_plural': 'Import rows',
                'ordering': ['row_number'],
                'unique_together': {('import_log', 'row_number')},
            },
        ),
    ]
