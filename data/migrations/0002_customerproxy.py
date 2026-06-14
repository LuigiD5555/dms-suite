from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('data', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='CustomerProxy',
            fields=[],
            options={'verbose_name': 'Customer', 'verbose_name_plural': 'Customers (Organizations)', 'proxy': True, 'indexes': [], 'constraints': []},
            bases=('data.organization',),
        ),
    ]
