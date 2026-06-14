"""
test_views_data.py — tests the data and autocomplete views.
"""
import pytest


@pytest.mark.django_db(databases=['default', 'enterprise_data'])
class TestDataViews:

    # Views that do not require login because OrganizationsView and PeopleView
    # do not have LoginRequiredMixin in the current code.
    VIEWS_WITHOUT_LOGIN = [
        '/customers/',
        '/organizations/',
        '/people/',
        '/personal/',
        '/employees/',
        '/candidates/',
    ]

    @pytest.mark.parametrize('url', VIEWS_WITHOUT_LOGIN)
    def test_does_not_return_404(self, client, url):
        """The data views must not return 404 — the URL must be registered."""
        response = client.get(url)
        assert response.status_code != 404, (
            f"{url} returned 404 - the URL is not registered in data/urls.py"
        )

    @pytest.mark.parametrize('url', VIEWS_WITHOUT_LOGIN)
    def test_does_not_return_500(self, client, url):
        """The data views must not return 500."""
        response = client.get(url)
        assert response.status_code != 500, (
            f"{url} returned 500 — there is an error in the view or template"
        )

    @pytest.mark.parametrize('url', VIEWS_WITHOUT_LOGIN)
    def test_session_request_does_not_return_error(self, client_plain, url):
        """No data view should return 4xx/5xx with an active session."""
        response = client_plain.get(url)
        assert response.status_code < 400, (
            f"{url} returned {response.status_code} with an active session"
        )

    def test_autocomplete_organizations(self, client_plain):
        response = client_plain.get('/autocomplete/organizations/')
        assert response.status_code == 200

    def test_autocomplete_zipcodes(self, client_plain):
        response = client_plain.get('/autocomplete/zip-codes/')
        assert response.status_code == 200

    def test_autocomplete_people(self, client_plain):
        response = client_plain.get('/autocomplete/people/')
        assert response.status_code == 200

    def test_autocomplete_organizations_with_query(self, client_plain):
        response = client_plain.get('/autocomplete/organizations/?q=test')
        assert response.status_code == 200

    def test_autocomplete_zipcodes_with_query(self, client_plain):
        response = client_plain.get('/autocomplete/zip-codes/?q=06600')
        assert response.status_code == 200
