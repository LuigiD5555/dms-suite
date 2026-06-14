import uuid
import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from .helpers import send_forget_password_mail
from django.views import View
from django.core.cache import cache
from django.db.models import Q
from users.models import CustomUser, User, Profile
from users.forms import CustomUserRegisterForm, CustomUserProfileForm
from django.urls import reverse
from django.utils import timezone


logger = logging.getLogger(__name__)
PASSWORD_RESET_TOKEN_TTL = timedelta(hours=1)


class PermissionRedirectMixin:
    def handle_no_permission(self):
        return redirect(self.get_login_url())


# Create your views here.
class LoginView(View):
    template_name = 'login/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # TODO: Make the try more specific, the try is too large
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')

            if not username or not password:
                messages.error(request, 'Username and password are required.')
                return redirect('/login/')

            user = authenticate(username=username, password=password)

            if user is None:
                messages.error(request, 'Invalid credentials.')
                return redirect('/login/')

            login(request, user)
            return redirect('/')
        # TODO: To define the exception
        except Exception as e:
            logger.exception('Login error')
            messages.error(request, 'Unable to sign in. Please try again.')
        return render(request, self.template_name)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('/')


class ForgetPasswordView(View):
    template_name = 'login/forget-password.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # TODO: Make the try more specific, the try is too large
        try:
            username = request.POST.get('username')

            # Generic message to prevent user enumeration.
            generic_message = 'If the user exists, an email with instructions will be sent.'
            user_obj = User.objects.filter(username=username).first()
            if not user_obj:
                messages.success(request, generic_message)
                return redirect('/forget-password/')

            token = str(uuid.uuid4())
            profile_obj, _ = Profile.objects.get_or_create(user=user_obj)
            profile_obj.forget_password_token = token
            profile_obj.forget_password_token_created_at = timezone.now()
            profile_obj.save(update_fields=['forget_password_token', 'forget_password_token_created_at'])
            send_forget_password_mail(user_obj.email, token)
            messages.success(request, generic_message)
            return redirect('/forget-password/')
        except Exception as e:
            logger.exception('Error requesting password recovery')
            messages.error(request, 'Unable to process the request.')
        return render(request, self.template_name)


class ChangePasswordView(View):
    template_name = 'login/change-password.html'

    def get(self, request, token):
        context = {}
        profile_obj = Profile.objects.filter(forget_password_token=token).first()
        if profile_obj and self._is_valid_token(profile_obj):
            context['user_id'] = profile_obj.user.id
        else:
            messages.error(request, 'The recovery link has expired or is invalid.')
        return render(request, self.template_name, context)

    @staticmethod
    def _is_valid_token(profile_obj):
        if not profile_obj.forget_password_token_created_at:
            return False
        return timezone.now() - profile_obj.forget_password_token_created_at <= PASSWORD_RESET_TOKEN_TTL

    def post(self, request, token):
        # TODO: Make the try more specific, the try is too large
        try:
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('reconfirm_password')
            user_id = request.POST.get('user_id')

            if user_id is None:
                messages.error(request, 'The recovery link is invalid.')
                return redirect(f'/change-password/{token}/')

            if new_password != confirm_password:
                messages.error(request, 'Passwords must match.')
                return redirect(f'/change-password/{token}/')

            profile_obj = Profile.objects.filter(forget_password_token=token, user_id=user_id).first()
            if not profile_obj or not self._is_valid_token(profile_obj):
                messages.error(request, 'The recovery link has expired or is invalid.')
                return redirect('/forget-password/')

            user_obj = User.objects.get(id=user_id)
            user_obj.set_password(new_password)
            user_obj.save()
            profile_obj.forget_password_token = ''
            profile_obj.forget_password_token_created_at = None
            profile_obj.save(update_fields=['forget_password_token', 'forget_password_token_created_at'])
            messages.success(request, 'Password updated successfully.')
            return redirect('/login/')
        except Exception as e:
            logger.exception('Error changing password')
            messages.error(request, 'Unable to change the password.')
        return render(request, self.template_name)


class HomeView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    template_name = 'home.html'

    def is_register_enabled(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        if user.groups.filter(name__in=['Superboss', 'Manager', 'Admin']).exists():
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_register_enabled'] = self.is_register_enabled()
        return context

    def get(self, request, *args, **kwargs):
        # The entire cache is not cleared on every visit because that invalidates other modules.
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class RegisterView(LoginRequiredMixin, PermissionRedirectMixin, UserPassesTestMixin, APIView):
    raise_exception = False
    login_url = '/login/'
    template_name = 'login/register.html'

    def test_func(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        if user.groups.filter(name__in=['Superboss', 'Manager', 'Admin']).exists():
            return True
        return False

    def get(self, request):
        form = CustomUserRegisterForm()
        is_register_enabled = self.test_func()
        context = {
            'form': form,
            'is_register_enabled': is_register_enabled,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = CustomUserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            # messages.success(request, 'User created successfully.')
            return redirect('/')
        else:
            messages.error(request, form.errors)

        is_register_enabled = self.test_func()
        context = {
            'form': form,
            'is_register_enabled': is_register_enabled,
        }
        return render(request, self.template_name, context)


class UsersView(LoginRequiredMixin, PermissionRedirectMixin, UserPassesTestMixin, TemplateView):
    raise_exception = False
    login_url = '/login/'

    def test_func(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        if user.groups.filter(name__in=['Superboss', 'Manager', 'Admin']).exists():
            return True
        return False

    def get(self, request, *args, **kwargs):
        users = CustomUser.objects.all()
        filter_text = request.GET.get('q', '')
        if filter_text:
            users = users.filter(
                Q(username__icontains=filter_text) |
                Q(email__icontains=filter_text) |
                Q(nombre__icontains=filter_text) |
                Q(apellido_paterno__icontains=filter_text) |
                Q(apellido_materno__icontains=filter_text) |
                Q(departamento__icontains=filter_text)
            )
        context = self.get_context_data()
        context['users'] = users
        context['filter_text'] = filter_text
        return render(request, 'user/users.html', context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_register_enabled'] = self.test_func()
        return context


class CustomUserProfileView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    template_name = 'user/user-profile.html'

    @staticmethod
    def is_register_enabled(user):
        # Check if the user is in any of the allowed groups
        return user.groups.filter(name__in=['Superboss', 'Manager', 'Admin']).exists()

    def get(self, request, **kwargs):
        """Display the profile editing form for the current user."""
        # The user ID (pk) is optional, we default to the logged-in user's ID
        pk = kwargs.get('pk', request.user.pk)

        # Retrieve the user object (404 if not found)
        user = get_object_or_404(CustomUser, pk=pk)

        # Ensure the current user can only edit their own profile unless authorized
        if user != request.user and not self.is_register_enabled(request.user):
            # If the user is trying to edit someone else's profile without permissions, deny access
            messages.error(request, 'You do not have permission to edit this profile.')
            return redirect(reverse('profile', kwargs={'pk': request.user.pk}))

        # Instantiate the form with the user data
        form = CustomUserProfileForm(instance=user)
        context = {
            'form': form,
            'is_register_enabled': self.is_register_enabled(request.user),
        }
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        """Handle profile updates."""
        pk = kwargs.get('pk', request.user.pk)
        user = get_object_or_404(CustomUser, pk=pk)

        # Ensure the current user can only update their own profile unless authorized
        if user != request.user and not self.is_register_enabled(request.user):
            messages.error(request, 'You do not have permission to edit this profile.')
            return redirect(reverse('profile', kwargs={'pk': request.user.pk}))

        # Handle form submission
        form = CustomUserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect(reverse('profile', kwargs={'pk': user.pk}))
        else:
            # Show error messages if form is invalid
            messages.error(request, 'There was an error updating the profile. Please try again.')

        # Re-render the form with errors
        context = {
            'form': form,
            'is_register_enabled': self.is_register_enabled(request.user),
        }
        return render(request, self.template_name, context)


class UserHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'user/history.html'
    login_url = '/login/'

    def is_register_enabled(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        if user.groups.filter(name__in=['Superboss', 'Manager', 'Admin']).exists():
            return True
        return False

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        user = get_object_or_404(CustomUser, pk=pk)
        form = CustomUserProfileForm(instance=user)
        is_register_enabled = self.is_register_enabled()
        context = {
            'form': form,
            'is_register_enabled': is_register_enabled,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = CustomUserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('/')
        else:
            messages.error(request, form.errors)

        is_register_enabled = self.is_register_enabled()
        context = {
            'form': form,
            'is_register_enabled': is_register_enabled,
        }
        return render(request, self.template_name, context)
