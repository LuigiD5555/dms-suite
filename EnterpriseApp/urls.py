from django.contrib import admin
from django.urls import path, include
from data.admin import *
from reports.generic_views import GenerateConfiguredReportView

urlpatterns = [
    path('api/v1/', include(('api.v1.urls', 'api'), namespace='v1')),
    path('reports/generate/', GenerateConfiguredReportView.as_view(), name='generic-report-generate'),
    path('admin/', admin.site.urls),
    path('', include('users.urls')),   # HomeView with LoginRequiredMixin goes first
    path('', include('data.urls')),
    path('', include('imports.urls')),
]
