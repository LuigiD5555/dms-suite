from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('data', '0002_customerproxy')]
    operations = [
        migrations.CreateModel(
            name='PersonalProxy',
            fields=[],
            options={
                'verbose_name': 'Personnel',
                'verbose_name_plural': 'Personnel (People)',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('data.person',),
        ),
    ]
