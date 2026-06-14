from django.core import validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imports', '0002_import_audit_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='importarexportar',
            name='archivo_csv',
            field=models.FileField(
                blank=True,
                default=None,
                null=True,
                upload_to='temporal/imports',
                validators=[validators.FileExtensionValidator(allowed_extensions=['csv'])],
                verbose_name='CSV file',
            ),
        ),
    ]
