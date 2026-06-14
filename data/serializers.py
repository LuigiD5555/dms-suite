from rest_framework import serializers

from data import models as data_models


def create_serializer(model, fields=None):
    class_name = f'{model.__name__}Serializer'
    meta_class = type('Meta', (object,), {'model': model, 'fields': fields or '__all__'})
    return type(class_name, (serializers.ModelSerializer,), {'Meta': meta_class})


ZipCodeSerializer = create_serializer(data_models.ZipCode)
OrganizationSerializer = create_serializer(data_models.Organization)
SiteSerializer = create_serializer(data_models.Site)
PersonSerializer = create_serializer(data_models.Person)
ContactSerializer = create_serializer(data_models.Contact)
AddressSerializer = create_serializer(data_models.Address)
DocumentCategorySerializer = create_serializer(data_models.DocumentCategory)
DocumentFileSerializer = create_serializer(data_models.DocumentFile)
DossierSerializer = create_serializer(data_models.Dossier)
DossierItemSerializer = create_serializer(data_models.DossierItem)
ProcessTemplateSerializer = create_serializer(data_models.ProcessTemplate)
ProcessStepTemplateSerializer = create_serializer(data_models.ProcessStepTemplate)
CaseSerializer = create_serializer(data_models.Case)
CaseStepSerializer = create_serializer(data_models.CaseStep)
AuditNoteSerializer = create_serializer(data_models.AuditNote)

# Compatibility aliases for older imports/documentation.
CustomerSerializer = OrganizationSerializer
LocationSerializer = SiteSerializer
PersonalSerializer = PersonSerializer
