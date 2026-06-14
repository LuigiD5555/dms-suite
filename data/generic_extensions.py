"""Extension examples for private/customer-specific apps.

Do not add industry-specific fields to the public core. Create a private Django
app and link it with OneToOne/ForeignKey relations to the generic public models.
"""

# Example:
#
# from django.db import models
#
# class CustomerSpecificPersonProfile(models.Model):
#     person = models.OneToOneField('data.Person', on_delete=models.CASCADE)
#     custom_status = models.CharField(max_length=50, blank=True, default='')
#     metadata = models.JSONField(default=dict, blank=True)
