from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'organizations', views.OrganizationViewSet, basename='v1-organization')
router.register(r'sites', views.SiteViewSet, basename='v1-site')
router.register(r'people', views.PersonViewSet, basename='v1-person')
router.register(r'contacts', views.ContactViewSet, basename='v1-contact')
router.register(r'addresses', views.AddressViewSet, basename='v1-address')
router.register(r'zip-codes', views.ZipCodeViewSet, basename='v1-zip-code')
router.register(r'document-categories', views.DocumentCategoryViewSet, basename='v1-document-category')
router.register(r'documents', views.DocumentFileViewSet, basename='v1-document')
router.register(r'dossiers', views.DossierViewSet, basename='v1-dossier')
router.register(r'dossier-items', views.DossierItemViewSet, basename='v1-dossier-item')
router.register(r'process-templates', views.ProcessTemplateViewSet, basename='v1-process-template')
router.register(r'process-step-templates', views.ProcessStepTemplateViewSet, basename='v1-process-step-template')
router.register(r'cases', views.CaseViewSet, basename='v1-case')
router.register(r'case-steps', views.CaseStepViewSet, basename='v1-case-step')
router.register(r'audit-notes', views.AuditNoteViewSet, basename='v1-audit-note')

router.register(r'imports/jobs', views.ImportarExportarViewSet, basename='v1-import-job')
router.register(r'imports/logs', views.ImportLogViewSet, basename='v1-import-log')
router.register(r'imports/rows', views.ImportRowViewSet, basename='v1-import-row')
router.register(r'reports/authenticity', views.ReportAuthenticityViewSet, basename='v1-report-authenticity')
router.register(r'users/users', views.UserViewSet, basename='v1-user')
router.register(r'users/profiles', views.ProfileViewSet, basename='v1-profile')
router.register(r'users/history', views.UserHistoryViewSet, basename='v1-user-history')

# Public compatibility aliases. They map to generic models, not to the old private schema.
router.register(r'data/customers', views.OrganizationViewSet, basename='v1-customer-compat')
router.register(r'data/personnel', views.PersonViewSet, basename='v1-personnel-compat')
router.register(r'data/personal', views.PersonViewSet, basename='v1-personal-compat')
router.register(r'data/locations', views.SiteViewSet, basename='v1-location-compat')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.HealthCheckView.as_view(), name='v1-health'),
    path('metadata/', views.APIMetadataView.as_view(), name='v1-metadata'),
    path('auth/token/', obtain_auth_token, name='v1-auth-token'),
    path('auth/me/', views.MeView.as_view(), name='v1-auth-me'),
    path('auth/session/', include('rest_framework.urls')),
]
