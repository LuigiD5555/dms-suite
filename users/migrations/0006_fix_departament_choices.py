from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('users', '0005_profile_password_reset_hardening')]
    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='departament',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Department', choices=[]),
        ),
    ]
