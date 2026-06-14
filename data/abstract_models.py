"""Reusable abstract base classes for optional extensions."""

from django.db import models


class AbstractTimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AbstractMetadataModel(models.Model):
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
