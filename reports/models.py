from django.db import models


# Create your models here.
class ReportAuthenticity(models.Model):
    authenticity_chain = models.CharField(max_length=64)
    report_name = models.CharField(max_length=255)
    content = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.report_name

    class Meta:
        verbose_name = 'Report Authenticity'
        verbose_name_plural = 'Report Authenticity Records'

