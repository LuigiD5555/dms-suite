from django.contrib import admin
from reports.models import ReportAuthenticity


# Register your models here.
@admin.register(ReportAuthenticity)
class ReportAuthenticityAdmin(admin.ModelAdmin):
    list_display = ('id', 'authenticity_chain', 'report_name', 'content', 'created_at')
    search_fields = ['authenticity_chain', 'report_name', 'created_at']


