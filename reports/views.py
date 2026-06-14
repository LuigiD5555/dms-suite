"""Generic report views for the public version.

All private/domain-specific report views were removed. Use
GenerateConfiguredReportView from reports.generic_views for template-driven
reports.
"""

from reports.generic_views import GenerateConfiguredReportView

__all__ = ['GenerateConfiguredReportView']
