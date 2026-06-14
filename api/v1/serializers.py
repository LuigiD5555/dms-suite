from django.contrib.auth import get_user_model
from rest_framework import serializers

from data import models as data_models
from imports import models as import_models
from reports import models as report_models
from users.models import Profile, UserHistory


class DisplayModelSerializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField(read_only=True)

    def get_display(self, obj):
        return str(obj)


def create_model_serializer(model, extra_read_only_fields=None):
    read_only_fields = set(extra_read_only_fields or [])
    for field in model._meta.fields:
        if getattr(field, 'auto_created', False) or getattr(field, 'primary_key', False):
            read_only_fields.add(field.name)
    meta = type('Meta', (), {'model': model, 'fields': '__all__', 'read_only_fields': tuple(sorted(read_only_fields))})
    return type(f'{model.__name__}V1Serializer', (DisplayModelSerializer,), {'Meta': meta, '__module__': __name__})


class CustomUserV1Serializer(DisplayModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    groups_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email', 'password', 'first_name', 'last_name', 'second_last_name',
            'departament', 'is_active', 'is_staff', 'is_superuser', 'groups', 'groups_display',
            'last_login', 'date_joined', 'display',
        )
        read_only_fields = ('id', 'last_login', 'date_joined', 'groups_display', 'display')
        extra_kwargs = {'password': {'write_only': True}, 'is_superuser': {'write_only': True}}

    def get_groups_display(self, obj):
        return list(obj.groups.values_list('name', flat=True))

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', [])
        user = get_user_model()(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        if groups:
            user.groups.set(groups)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        if groups is not None:
            user.groups.set(groups)
        return user


ZipCodeV1Serializer = create_model_serializer(data_models.ZipCode)
OrganizationV1Serializer = create_model_serializer(data_models.Organization)
SiteV1Serializer = create_model_serializer(data_models.Site)
PersonV1Serializer = create_model_serializer(data_models.Person)
ContactV1Serializer = create_model_serializer(data_models.Contact)
AddressV1Serializer = create_model_serializer(data_models.Address)
DocumentCategoryV1Serializer = create_model_serializer(data_models.DocumentCategory)
DocumentFileV1Serializer = create_model_serializer(data_models.DocumentFile)
DossierV1Serializer = create_model_serializer(data_models.Dossier)
DossierItemV1Serializer = create_model_serializer(data_models.DossierItem)
ProcessTemplateV1Serializer = create_model_serializer(data_models.ProcessTemplate)
ProcessStepTemplateV1Serializer = create_model_serializer(data_models.ProcessStepTemplate)
CaseV1Serializer = create_model_serializer(data_models.Case)
CaseStepV1Serializer = create_model_serializer(data_models.CaseStep)
AuditNoteV1Serializer = create_model_serializer(data_models.AuditNote)

ImportarExportarV1Serializer = create_model_serializer(import_models.ImportarExportar, extra_read_only_fields={
    'status', 'rows_processed', 'rows_success', 'rows_error', 'error_detail', 'imported_at', 'created_at',
})
ImportLogV1Serializer = create_model_serializer(import_models.ImportLog)
ImportRowV1Serializer = create_model_serializer(import_models.ImportRow)
ReportAuthenticityV1Serializer = create_model_serializer(report_models.ReportAuthenticity)
ProfileV1Serializer = create_model_serializer(Profile)
UserHistoryV1Serializer = create_model_serializer(UserHistory)

# Compatibility aliases for old API names.
CustomerV1Serializer = OrganizationV1Serializer
LocationV1Serializer = SiteV1Serializer
PersonalV1Serializer = PersonV1Serializer
