"""
Regression tests for the "Not Found inside the iframe" bug.

The /customers/, /candidates/, and /employees/ views returned 200 because the
public URL resolved and rendered its template. However, those templates contain
an iframe that points to a Django admin URL:

    customer/customers.html  ->  <iframe src="/admin/data/customer/">
    personal/personal.html   ->  <iframe src="/admin/data/personal/">   (employees and candidates)

The admin proxies were named `CustomerProxy` and `PersonalProxy`. In Django,
model_name, the lowercase class name, is the admin URL segment, so the admin
exposed /admin/data/customerproxy/ and /admin/data/personalproxy/.
The iframe requested /admin/data/customer/ -> 404 INSIDE the iframe -> the user saw
"Not Found" even though the outer page returned 200.

The old tests only checked that the public URL did not return 404 or 500. These
tests cover the complete request chain:

    public URL -> rendered HTML -> iframe src -> admin URL does not return 404
"""
import re

import pytest

# (public_url, fragment that the iframe src must contain)
VIEWS_WITH_IFRAMES = [
    ('/customers/',  '/admin/data/customer/'),
    ('/candidates/', '/admin/data/personal/'),
    ('/employees/',  '/admin/data/personal/'),
]

IFRAME_SRC_RE = re.compile(r'<iframe[^>]*\bsrc="([^"]+)"', re.IGNORECASE)


def _iframe_srcs(html):
    """Extract every iframe src from rendered HTML."""
    return IFRAME_SRC_RE.findall(html)


@pytest.mark.django_db(databases=['default', 'enterprise_data'])
class TestIframeAdminTargets:
    """Validate the public view -> iframe -> admin URL chain."""

    @pytest.mark.parametrize('public_url, admin_target', VIEWS_WITH_IFRAMES)
    def test_public_view_returns_200(self, client_superuser, public_url, admin_target):
        response = client_superuser.get(public_url)
        assert response.status_code == 200, (
            f"{public_url} returned {response.status_code} instead of 200."
        )

    @pytest.mark.parametrize('public_url, admin_target', VIEWS_WITH_IFRAMES)
    def test_iframe_points_to_expected_url(self, client_superuser, public_url, admin_target):
        """The template must continue pointing to the expected admin target."""
        response = client_superuser.get(public_url)
        srcs = _iframe_srcs(response.content.decode('utf-8'))
        assert any(admin_target in s for s in srcs), (
            f"{public_url}: no iframe points to {admin_target}.\n"
            f"iframes found: {srcs or '(none)'}"
        )

    @pytest.mark.parametrize('public_url, admin_target', VIEWS_WITH_IFRAMES)
    def test_iframe_target_does_not_return_404(self, client_superuser, public_url, admin_target):
        """
        THE KEY TEST: the admin URL loaded by the iframe must EXIST.

        The test extracts the actual src from rendered HTML and requests that
        URL. If the proxy model_name stops matching the
        iframe segment, this test fails with an actionable message.
        """
        response = client_superuser.get(public_url)
        admin_srcs = [s for s in _iframe_srcs(response.content.decode('utf-8'))
                      if s.startswith('/admin/')]
        assert admin_srcs, f"{public_url}: no iframe targeting /admin/."

        for src in admin_srcs:
            inner = client_superuser.get(src)
            assert inner.status_code != 404, (
                f"The iframe on {public_url} loads '{src}' and returned 404.\n"
                f"Typical root cause: the proxy CLASS name in data/admin.py "
                f"does not match the URL segment.\n"
                f"In Django, model_name (the lowercase class name) IS the admin URL: "
                f"the class must be named 'Customer' for /admin/data/customer/, "
                f"not 'CustomerProxy', which produces /admin/data/customerproxy/."
            )


class TestProxyModelNamesMatchIframe:
    """
    Model-level root cause, without database or HTTP: checks that the admin registers
    a model whose model_name exactly matches the iframe target. This is the most
    inexpensive test and provides the clearest diagnosis if the proxy is renamed.
    """

    # model_name (in lowercase) expected by each iframe under the app 'data'
    REQUIRED_MODEL_NAMES = ['customer', 'personal']

    def _data_admin_model_names(self):
        # Imports inside the function: Django is not configured yet at module level
        # when pytest collects tests; see tests/conftest.py.
        from django.contrib import admin
        import data.admin  # noqa: F401 - force proxy registration
        return {
            m._meta.model_name
            for m in admin.site._registry
            if m._meta.app_label == 'data'
        }

    @pytest.mark.parametrize('model_name', REQUIRED_MODEL_NAMES)
    def test_admin_registers_model(self, model_name):
        registered_models = self._data_admin_model_names()
        assert model_name in registered_models, (
            f"No '{model_name}' model is registered in the data admin.\n"
            f"The iframe URL /admin/data/{model_name}/ requires a class named "
            f"exactly '{model_name.capitalize()}' in data/admin.py.\n"
            f"Currently registered data models: {sorted(registered_models)}"
        )
