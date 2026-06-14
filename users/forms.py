from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group
from django import forms
from users.models import (
    CustomUser, DEPARTMENT_CHOICES
)


class CustomUserRegisterForm(UserCreationForm):
    # Custom User creation form.
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='First name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Last name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    second_last_name = forms.CharField(label='Second last name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    department = forms.ChoiceField(label='Department', choices=DEPARTMENT_CHOICES, widget=forms.Select(attrs={'class': 'select'}))
    groups = forms.ModelMultipleChoiceField(
        label='Account types', queryset=Group.objects.all(),
        widget=FilteredSelectMultiple("Groups", is_stacked=False), required=False, )
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'second_last_name', 'email', 'departament', 'is_superuser',
                  'is_staff', 'groups')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_superuser_default_help_text = CustomUser._meta.get_field('is_superuser').help_text
        is_staff_default_help_text = CustomUser._meta.get_field('is_staff').help_text
        # permissions_help_text = CustomUser._meta.get_field('user_permissions').help_text
        groups_help_text = CustomUser._meta.get_field('groups').help_text
        self.fields['is_superuser'].help_text = '<div class="help">{}</div>'.format(is_superuser_default_help_text)
        self.fields['is_staff'].help_text = '<div class="help">{}</div>'.format(is_staff_default_help_text)
        self.fields[
            'groups'].help_text = ('<div class="help">{} Hold "Control" or "Command" on a Mac '
                                   'to select more than one.</div>').format(groups_help_text)
        # self.fields['permissions'].help_text = '<div class="help" id="id_permissions_helptext">{}.
        # Hold "Control" on a PC or "Command" on macOS to select more than one.</div>'.format(permissions_help_text)

    def clean_password2(self):
        # Check that both passwords match.
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()  # Save many-to-many relationships (permissions)
        return user


class CustomUserProfileForm(UserChangeForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    second_last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'value': 'existing_password'
        }
    ))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    departament = forms.ChoiceField(label='Department', choices=DEPARTMENT_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'second_last_name', 'email', 'departament')

