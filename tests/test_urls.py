"""
test_urls.py — verifies that project URLs resolve and respond.
"""
import pytest
from django.urls import reverse, NoReverseMatch


class TestUrlResolution:
    """Verifies named URL resolution — without database or templates."""

    NAMED_URLS = [
        'home', 'login', 'logout', 'forget_password', 'register', 'users',
        'organizations', 'people', 'customers', 'personal',
        'employees', 'candidates',
        'organization-autocomplete', 'zipcode-autocomplete', 'person-autocomplete',
    ]

    @pytest.mark.parametrize('name', NAMED_URLS)
    def test_named_url_resolves(self, name):
        try:
            url = reverse(name)
            assert url.startswith('/')
        except NoReverseMatch:
            pytest.fail(
                f"URL '{name}' is not registered.\n"
                f"Add it to data/urls.py or users/urls.py as appropriate."
            )


@pytest.mark.django_db(databases=['default', 'enterprise_data'])
class TestUrlResponses:
    """Verify that the main URLs do not return 404 or 500."""

    CRITICAL_URLS = [
        '/customers/',
        '/candidates/',
        '/employees/',
        '/organizations/',
        '/people/',
        '/personal/',
    ]

    @pytest.mark.parametrize('url', CRITICAL_URLS)
    def test_url_does_not_return_404(self, client_superuser, url):
        """No critical URL should return 404."""
        response = client_superuser.get(url)
        assert response.status_code != 404, (
            f"{url} returned 404.\n"
            f"Verify that it is registered in data/urls.py."
        )

    @pytest.mark.parametrize('url', CRITICAL_URLS)
    def test_url_does_not_return_500(self, client_superuser, url):
        """No critical URL should return 500."""
        response = client_superuser.get(url)
        assert response.status_code != 500, (
            f"{url} returned 500.\n"
            f"Review data/views.py and the corresponding template."
        )

    @pytest.mark.parametrize('url', CRITICAL_URLS)
    def test_url_returns_200(self, client_superuser, url):
        """All critical URLs should return 200 for a superuser."""
        response = client_superuser.get(url)
        assert response.status_code == 200, (
            f"{url} returned {response.status_code} instead of 200."
        )

    def test_admin_data_customer_is_registered(self, client_superuser):
        """/admin/data/customer/ must exist because customers.html uses it."""
        response = client_superuser.get('/admin/data/customer/')
        assert response.status_code != 404, (
            "/admin/data/customer/ returned 404.\n"
            "The proxy model_name defines the URL: the class in data/admin.py must "
            "be named 'Customer' (not 'CustomerProxy', which would produce /admin/data/customerproxy/)."
        )

    def test_admin_data_personal_is_registered(self, client_superuser):
        """/admin/data/personal/ must exist because personal.html uses it."""
        response = client_superuser.get('/admin/data/personal/')
        assert response.status_code != 404, (
            "/admin/data/personal/ returned 404.\n"
            "The proxy model_name defines the URL: the class in data/admin.py must "
            "be named 'Personal' (not 'PersonalProxy', which would produce /admin/data/personalproxy/)."
        )
