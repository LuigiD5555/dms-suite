"""
Management command: create_test_users
Creates test users for pytest. Development only.

    python manage.py create_test_users

Credentials:
    admin      / admin1234      - superuser
    staff      / staff1234      - is_staff
    normal     / normal1234     - no permissions
    superboss  / superboss1234  - Superboss group
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

TEST_USERS = [
    ('admin',     'admin1234',     'admin@test.com',     True,  True,  []),
    ('staff',     'staff1234',     'staff@test.com',     False, True,  []),
    ('normal',    'normal1234',    'normal@test.com',    False, False, []),
    ('superboss', 'superboss1234', 'superboss@test.com', False, False, ['Superboss']),
]


class Command(BaseCommand):
    help = 'Creates test users for pytest (development only)'

    def handle(self, *args, **options):
        self.stdout.write('Creating test users...\n')
        for username, password, email, is_superuser, is_staff, groups in TEST_USERS:
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  [already exists] {username}')
                continue
            if is_superuser:
                user = User.objects.create_superuser(
                    username=username, password=password, email=email
                )
            else:
                user = User.objects.create_user(
                    username=username, password=password,
                    email=email, is_staff=is_staff
                )
            for group_name in groups:
                group, _ = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f'  [created]    {username} / {password}'))

        self.stdout.write(self.style.SUCCESS('\nTest users are ready.'))
        self.stdout.write('Credentials for http://localhost:20001/login/:')
        for username, password, *_ in TEST_USERS:
            self.stdout.write(f'  {username:12s} / {password}')
