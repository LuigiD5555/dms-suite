from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from data import models as data_models
from imports import models as import_models
from reports import models as report_models
from users.models import Profile, UserHistory
from . import serializers as v1_serializers


class HealthCheckView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok', 'service': 'enterprise-dms-core', 'version': 'v1'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(v1_serializers.CustomUserV1Serializer(request.user, context={'request': request}).data)


class APIMetadataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = []
        for model in apps.get_models():
            if model._meta.app_label not in {'data', 'imports', 'reports', 'users'}:
                continue
            if model._meta.proxy or model._meta.abstract:
                continue
            fields = []
            for field in model._meta.fields:
                relation = None
                if getattr(field, 'remote_field', None) and field.remote_field and field.remote_field.model:
                    relation = f'{field.remote_field.model._meta.app_label}.{field.remote_field.model.__name__}'
                fields.append({
                    'name': field.name,
                    'type': field.get_internal_type(),
                    'required': not getattr(field, 'blank', False) and not getattr(field, 'null', False),
                    'read_only': getattr(field, 'primary_key', False) or getattr(field, 'auto_created', False),
                    'relation': relation,
                    'choices': [
                        {'value': choice_value, 'label': choice_label}
                        for choice_value, choice_label in (getattr(field, 'choices', None) or [])
                        if not isinstance(choice_label, (list, tuple))
                    ],
                    'max_length': getattr(field, 'max_length', None),
                })
            payload.append({
                'app': model._meta.app_label,
                'model': model.__name__,
                'verbose_name': str(model._meta.verbose_name),
                'verbose_name_plural': str(model._meta.verbose_name_plural),
                'fields': fields,
            })
        return Response(payload)


def build_viewset(model, serializer_class, read_only=False):
    base_mixins = (
        (mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet)
        if read_only else
        (mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet)
    )
    return type(
        f'{model.__name__}ViewSet',
        base_mixins,
        {
            '__module__': __name__,
            'queryset': model.objects.all(),
            'serializer_class': serializer_class,
            'permission_classes': [IsAuthenticated],
            'parser_classes': [JSONParser, FormParser, MultiPartParser],
            'filter_backends': [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter],
            'ordering_fields': '__all__',
            'ordering': ['id'] if any(field.name == 'id' for field in model._meta.fields) else [],
        },
    )


class OrganizationViewSet(build_viewset(data_models.Organization, v1_serializers.OrganizationV1Serializer)):
    search_fields = ['trade_name', 'legal_name', 'tax_id', 'primary_email']
    filterset_fields = ['id', 'is_active', 'organization_type']
    ordering_fields = ['id', 'trade_name', 'legal_name', 'created_at']
    ordering = ['trade_name', 'legal_name']


class PersonViewSet(build_viewset(data_models.Person, v1_serializers.PersonV1Serializer)):
    search_fields = ['external_id', 'first_name', 'last_name', 'second_last_name', 'email', 'role', 'department', 'organization__trade_name']
    filterset_fields = ['id', 'organization', 'site', 'status', 'department']
    ordering_fields = ['id', 'external_id', 'first_name', 'last_name', 'created_at', 'start_date']
    ordering = ['last_name', 'first_name']

    @action(detail=False, methods=['get'])
    def active(self, request):
        return self._filtered_list(self.get_queryset().filter(status=data_models.Person.STATUS_ACTIVE))

    @action(detail=False, methods=['get'])
    def candidates(self, request):
        return self._filtered_list(self.get_queryset().filter(status=data_models.Person.STATUS_CANDIDATE))

    def _filtered_list(self, queryset):
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DocumentFileViewSet(build_viewset(data_models.DocumentFile, v1_serializers.DocumentFileV1Serializer)):
    search_fields = ['title', 'category__name', 'organization__trade_name', 'person__first_name', 'person__last_name']
    filterset_fields = ['id', 'category', 'organization', 'site', 'person', 'status']
    ordering_fields = ['id', 'title', 'expiration_date', 'created_at', 'updated_at']
    ordering = ['expiration_date', '-created_at']


SiteViewSet = build_viewset(data_models.Site, v1_serializers.SiteV1Serializer)
ContactViewSet = build_viewset(data_models.Contact, v1_serializers.ContactV1Serializer)
AddressViewSet = build_viewset(data_models.Address, v1_serializers.AddressV1Serializer)
ZipCodeViewSet = build_viewset(data_models.ZipCode, v1_serializers.ZipCodeV1Serializer)
DocumentCategoryViewSet = build_viewset(data_models.DocumentCategory, v1_serializers.DocumentCategoryV1Serializer)
DossierViewSet = build_viewset(data_models.Dossier, v1_serializers.DossierV1Serializer)
DossierItemViewSet = build_viewset(data_models.DossierItem, v1_serializers.DossierItemV1Serializer)
ProcessTemplateViewSet = build_viewset(data_models.ProcessTemplate, v1_serializers.ProcessTemplateV1Serializer)
ProcessStepTemplateViewSet = build_viewset(data_models.ProcessStepTemplate, v1_serializers.ProcessStepTemplateV1Serializer)
CaseViewSet = build_viewset(data_models.Case, v1_serializers.CaseV1Serializer)
CaseStepViewSet = build_viewset(data_models.CaseStep, v1_serializers.CaseStepV1Serializer)
AuditNoteViewSet = build_viewset(data_models.AuditNote, v1_serializers.AuditNoteV1Serializer)

ImportarExportarViewSet = build_viewset(import_models.ImportarExportar, v1_serializers.ImportarExportarV1Serializer)
ImportLogViewSet = build_viewset(import_models.ImportLog, v1_serializers.ImportLogV1Serializer, read_only=True)
ImportRowViewSet = build_viewset(import_models.ImportRow, v1_serializers.ImportRowV1Serializer, read_only=True)
ReportAuthenticityViewSet = build_viewset(report_models.ReportAuthenticity, v1_serializers.ReportAuthenticityV1Serializer, read_only=True)


class UserViewSet(build_viewset(get_user_model(), v1_serializers.CustomUserV1Serializer)):
    permission_classes = [IsAdminUser]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'second_last_name']
    filterset_fields = ['id', 'is_active', 'is_staff', 'is_superuser', 'departament']
    ordering_fields = ['id', 'username', 'email', 'date_joined', 'last_login']
    ordering = ['username']


ProfileViewSet = build_viewset(Profile, v1_serializers.ProfileV1Serializer)
UserHistoryViewSet = build_viewset(UserHistory, v1_serializers.UserHistoryV1Serializer, read_only=True)

# Compatibility aliases for previous endpoint classes.
CustomerViewSet = OrganizationViewSet
PersonalViewSet = PersonViewSet
LocationViewSet = SiteViewSet
