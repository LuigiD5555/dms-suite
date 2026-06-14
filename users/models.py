from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from EnterpriseApp.utility_toolkit.system_variables import DEPARTMENT_CHOICES
from django.contrib.auth import get_user_model


# Create your models here.
class CustomUserManager(BaseUserManager):
    """
    Custom users model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        if not extra_fields.get('name'):
            raise ValueError('The Name must be set')
        if not password:
            raise ValueError('The Password must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='First name')
    last_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='Last name')
    second_last_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='Second last name')
    departament = models.PositiveSmallIntegerField(choices=DEPARTMENT_CHOICES, blank=True, null=True, verbose_name='Department')

    def get_full_name(self):
        return f'{self.last_name} {self.second_last_name} {self.first_name}'

    class Meta:
        managed = True
        verbose_name = 'User'
        verbose_name_plural = 'Users'


User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    forget_password_token = models.CharField(max_length=100, blank=True, default='')
    forget_password_token_created_at = models.DateTimeField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class UserHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    action = models.CharField(max_length=255, verbose_name='Action')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Date')
    model = models.CharField(max_length=255, verbose_name='Model')
    object_id = models.CharField(max_length=255, verbose_name='Object ID')
    change = models.TextField(verbose_name='Changes')
    ip_address = models.GenericIPAddressField(default=None, null=True, blank=True, verbose_name='IP address')
    user_agent = models.CharField(max_length=255, blank=True, null=True, verbose_name='Browser')

    def __str__(self):
        return f'{self.user} - {self.action}'

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'History'
        verbose_name_plural = 'Histories'
