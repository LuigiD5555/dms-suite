"""
test_models.py — tests the main models.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


@pytest.mark.django_db
class TestCustomUser:

    def test_crear_usuario_basico(self, plain_user):
        assert plain_user.username == 'normal'
        assert plain_user.is_active is True
        assert plain_user.is_superuser is False
        assert plain_user.is_staff is False

    def test_crear_superusuario(self, superuser):
        assert superuser.is_superuser is True
        assert superuser.is_staff is True

    def test_full_name(self, db):
        user = User.objects.create_user(
            username='jdoe', password='pass1234', email='jdoe@test.com',
            first_name='John', last_name='Smith', second_last_name='Taylor',
        )
        full_name = user.get_full_name()
        assert 'John' in full_name
        assert 'Smith' in full_name

    def test_grupo_superboss(self, superboss_user):
        assert superboss_user.groups.filter(name='Superboss').exists()

    def test_password_hasheado(self, plain_user):
        assert not plain_user.password.startswith('normal1234')
        assert plain_user.check_password('normal1234')


@pytest.mark.django_db(databases=['enterprise_data'])
class TestZipCode:

    def test_crear_zipcode(self):
        from data.models import ZipCode
        zc = ZipCode.objects.using('enterprise_data').create(
            zip_code='06600', settlement='Juarez', municipality='Cuauhtemoc',
            region='CDMX', city='CDMX', country='Mexico',
            normalized_settlement='JUAREZ',
        )
        assert zc.pk is not None
        assert zc.zip_code == '06600'

    def test_busqueda_normalizada(self):
        from data.models import ZipCode
        ZipCode.objects.using('enterprise_data').create(
            zip_code='06600', settlement='Juarez',
            normalized_settlement='JUAREZ', municipality='Cuauhtemoc',
            region='CDMX', city='CDMX', country='Mexico',
        )
        result = ZipCode.objects.using('enterprise_data').filter(
            normalized_settlement__icontains='JUAREZ'
        )
        assert result.exists()

    def test_zipcode_str_contiene_codigo(self):
        from data.models import ZipCode
        zc = ZipCode.objects.using('enterprise_data').create(
            zip_code='01000', settlement='San Angel',
            normalized_settlement='SAN ANGEL', municipality='Alvaro Obregon',
            region='CDMX', city='CDMX', country='Mexico',
        )
        # We only verify that the ZIP code appears in str(),
        # without assuming the exact format
        assert '01000' in str(zc)


@pytest.mark.django_db(databases=['enterprise_data'])
class TestOrganizacion:

    def test_crear_organizacion(self):
        from data.models import Organization
        org = Organization.objects.using('enterprise_data').create(
            legal_name='Example Company S.A. de C.V.',
            trade_name='Example Company',
        )
        assert org.pk is not None
        assert org.is_active is True

    def test_organizacion_str_contiene_full_name(self):
        from data.models import Organization
        org = Organization.objects.using('enterprise_data').create(
            legal_name='ACME S.A.',
            trade_name='ACME',
        )
        # str(org) returns trade_name as it was saved
        # we use the actual value instead of assuming uppercase conversion
        assert org.trade_name in str(org)

    def test_organizacion_activa_por_defecto(self):
        from data.models import Organization
        org = Organization.objects.using('enterprise_data').create(
            legal_name='Test Legal', trade_name='Test',
        )
        assert org.is_active is True


@pytest.mark.django_db(databases=['enterprise_data'])
class TestPersona:

    def test_crear_persona(self):
        from data.models import Organization, Person
        org = Organization.objects.using('enterprise_data').create(
            legal_name='Example Company S.A.', trade_name='Example Company',
        )
        person = Person.objects.using('enterprise_data').create(
            organization=org, first_name='Alice', last_name='Jones',
        )
        assert person.pk is not None
        assert 'Alice' in person.get_full_name()


@pytest.mark.django_db
class TestProfile:

    def test_profile_str(self, plain_user):
        from users.models import Profile
        profile = Profile.objects.create(user=plain_user)
        assert plain_user.username in str(profile)

    def test_profile_token_vacio_por_defecto(self, plain_user):
        from users.models import Profile
        profile = Profile.objects.create(user=plain_user)
        assert profile.forget_password_token == ''
        assert profile.forget_password_token_created_at is None
