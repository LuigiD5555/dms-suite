from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create the Superboss group and assign all permissions to it'

    def handle(self, *args, **options):
        group_name = 'Superboss'
        group, created = Group.objects.get_or_create(name=group_name)

        if created:
            content_types = ContentType.objects.all()
            permissions = Permission.objects.filter(content_type__in=content_types)
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS('Superboss group created successfully!'))
        else:
            self.stdout.write(self.style.SUCCESS('Superboss group already exists. No action taken.'))
