"""Neutral admin report actions.

Domain-specific report actions were removed from the public version.
Use reports/config.py and reports/generic_views.py for configurable reports.
"""

from django.contrib import messages


def report_action_placeholder(modeladmin, request, queryset):
    messages.info(request, 'Business-specific reports were removed from the public version. Use the configurable report generator.')


report_action_placeholder.short_description = 'Generate configurable report'
