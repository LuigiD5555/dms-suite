# Generated manually for Enterprise DMS password reset hardening.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_customuser_departament'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='forget_password_token',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='forget_password_token_created_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
