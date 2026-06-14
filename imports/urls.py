from django.urls import path
from imports import views

urlpatterns = [
    path('download-imports-template/', views.download_csv_template, name='download_import_template'),
]
