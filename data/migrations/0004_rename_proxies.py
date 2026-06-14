from django.db import migrations


class Migration(migrations.Migration):
    """
    Rename proxy models so their model_name matches the admin URLs used by the
    template iframes:

        CustomerProxy  -> Customer   => /admin/data/customer/
        PersonalProxy -> Personal  => /admin/data/personal/

    Proxy models do not have their own tables; they share the table of their
    base model. RenameModel on a proxy only updates
    the state/ContentType and does not execute ALTER TABLE. This operation does not risk data.
    """

    dependencies = [
        ('data', '0003_personalproxy'),
    ]

    operations = [
        migrations.RenameModel(old_name='CustomerProxy', new_name='Customer'),
        migrations.RenameModel(old_name='PersonalProxy', new_name='Personal'),
    ]
