"""
Fixtures shared by all tests.

Django imports belong INSIDE each fixture, never at module level.
Reason: tests/conftest.py is imported before pytest_configure() in the root
conftest.py configures Django. A module-level import from django.contrib.*
triggers apps.check_apps_ready() and fails with
ImproperlyConfigured because settings are not loaded yet.
"""
import pytest


@pytest.fixture
def superuser(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_superuser(
        username='admin',
        password='admin1234',
        email='admin@test.com',
    )


@pytest.fixture
def staff_user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='staff',
        password='staff1234',
        email='staff@test.com',
        is_staff=True,
    )


@pytest.fixture
def plain_user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='normal',
        password='normal1234',
        email='normal@test.com',
    )


@pytest.fixture
def superboss_user(db):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    User = get_user_model()
    group, _ = Group.objects.get_or_create(name='Superboss')
    user = User.objects.create_user(
        username='superboss',
        password='superboss1234',
        email='superboss@test.com',
    )
    user.groups.add(group)
    return user


@pytest.fixture
def client_superuser(client, superuser):
    client.force_login(superuser)
    return client


@pytest.fixture
def client_plain(client, plain_user):
    client.force_login(plain_user)
    return client


@pytest.fixture
def client_superboss(client, superboss_user):
    client.force_login(superboss_user)
    return client
