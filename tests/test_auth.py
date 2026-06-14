"""
test_auth.py — tests the complete authentication and access-control flow.
"""
import pytest


@pytest.mark.django_db
class TestLogin:

    def test_login_get_returns_200(self, client):
        """GET /login/ always returns 200."""
        response = client.get('/login/')
        assert response.status_code == 200

    def test_valid_login(self, client, plain_user):
        """Login with valid credentials redirects to /."""
        response = client.post('/login/', {'username': 'normal', 'password': 'normal1234'})
        assert response.status_code == 302
        assert response['Location'] == '/'

    def test_invalid_login_does_not_authenticate(self, client):
        """Login with invalid credentials does not redirect home."""
        response = client.post('/login/', {'username': 'noexiste', 'password': 'mal'})
        # Remain on login or redirect back to /login/.
        assert response.status_code in (200, 302)
        if response.status_code == 302:
            assert 'login' in response['Location']

    def test_root_without_session_redirects_to_login(self, client):
        """/ without a session must redirect to /login/, not display a blank page."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_root_with_session_returns_200(self, client_plain):
        """/ with an active session must return 200."""
        response = client_plain.get('/')
        assert response.status_code == 200

    def test_logout_redirects(self, client_plain):
        """Logout redirects."""
        response = client_plain.get('/logout/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestUserPermissions:

    def test_users_without_session_redirects_to_login(self, client):
        """/users/ redirects to /login/ without a session."""
        response = client.get('/users/')
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_users_returns_200_for_superuser(self, client_superuser):
        """/users/ with a superuser must return 200.
        A 500 indicates that UsersView.test_func() does not assign the user.
        A 403 indicates that UsersView does not set raise_exception to False.
        """
        response = client_superuser.get('/users/')
        assert response.status_code == 200, (
            f"Received {response.status_code}. Review users/views.py:\n"
            "  class UsersView:\n"
            "      raise_exception = False   # ← add this\n"
            "      def test_func(self):\n"
            "          user = self.request.user   # ← must appear BEFORE it is used\n"
            "          if user.is_superuser or user.is_staff:\n"
            "              return True\n"
        )

    def test_users_returns_200_for_staff(self, client, staff_user):
        """is_staff must also have access to /users/."""
        client.force_login(staff_user)
        response = client.get('/users/')
        assert response.status_code == 200

    def test_users_returns_200_for_superboss_group(self, client_superboss):
        """The Superboss group must access /users/."""
        response = client_superboss.get('/users/')
        assert response.status_code == 200

    def test_users_redirects_user_without_permission(self, client_plain):
        """/users/ for a user without permissions must redirect (302), not return 403.
        A failure indicates that UsersView must set raise_exception to False.
        """
        response = client_plain.get('/users/')
        assert response.status_code != 403, (
            "Received 403. Add this in users/views.py:\n"
            "  class UsersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):\n"
            "      raise_exception = False   # ← this line\n"
        )
        assert response.status_code == 302

    def test_register_does_not_return_403_without_permission(self, client_plain):
        """/register/ for a user without permissions must not return 403.
        A failure indicates that RegisterView must set raise_exception to False.
        """
        response = client_plain.get('/register/')
        assert response.status_code != 403, (
            "Received 403. Add this in users/views.py:\n"
            "  class RegisterView(LoginRequiredMixin, UserPassesTestMixin, APIView):\n"
            "      raise_exception = False   # ← this line\n"
        )
        assert response.status_code == 302

    def test_register_returns_200_for_superuser(self, client_superuser):
        """/register/ with a superuser must return 200."""
        response = client_superuser.get('/register/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestIsRegisterEnabled:
    """Verify is_register_enabled for users with permissions."""

    def test_superuser_has_register_enabled(self, client_superuser):
        response = client_superuser.get('/')
        assert response.status_code == 200
        assert response.context.get('is_register_enabled') is True, (
            "is_register_enabled is False for a superuser. "
            "Review is_register_enabled() in HomeView; it must include:\n"
            "  if user.is_superuser or user.is_staff: return True"
        )

    def test_plain_user_does_not_have_register_enabled(self, client_plain):
        response = client_plain.get('/')
        assert response.status_code == 200
        assert response.context.get('is_register_enabled') is False

    def test_superboss_has_register_enabled(self, client_superboss):
        response = client_superboss.get('/')
        assert response.status_code == 200
        assert response.context.get('is_register_enabled') is True
