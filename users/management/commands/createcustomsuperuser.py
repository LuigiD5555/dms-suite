from django.contrib.auth.management.commands.createsuperuser import (
    Command as CreatesuperuserCommand,
)
from django.core.management.base import CommandError
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist


class Command(CreatesuperuserCommand):
    help = "Create a superuser with automatically generated email based on the username"

    def handle(self, *args, **options):
        # Verifying if the username is available in the options
        username = options.get("username")

        # If a username is not provided in the options, we ask the user to input it
        if not username:
            username = input("Username: ")
            options["username"] = username

        # Generating the email based on the username if one was not provided
        if not options.get("email"):
            generated_email = f"{slugify(username)}@enterprise.com"
            options["email"] = generated_email

        # Calling the original superuser creation method
        super().handle(*args, **options)

        # Assigning the superuser to the 'Superboss' group
        self.add_to_superboss_group(options["username"])

        # Display a success message with the email address used.
        self.stdout.write(
            self.style.SUCCESS(
                f'Superuser created successfully! Email: {options["email"]}'
            )
        )

    def add_to_superboss_group(self, username):
        """
        Add the created superuser to the 'Superboss' group
        """
        User = get_user_model()

        # Fetch the user based on the username
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            raise CommandError(f"User with username '{username}' not found.")

        # Fetch or create the 'Superboss' group
        group, created = Group.objects.get_or_create(name='Superboss')

        # Add the user to the 'Superboss' group
        user.groups.add(group)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f"User '{username}' added to 'Superboss' group.")
        )
