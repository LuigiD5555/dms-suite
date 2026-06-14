from django.contrib import admin

from data.models import (
    Address,
    AuditNote,
    Case,
    CaseStep,
    Contact,
    DocumentCategory,
    DocumentFile,
    Dossier,
    DossierItem,
    Organization,
    Person,
    ProcessStepTemplate,
    ProcessTemplate,
    Site,
    ZipCode,
)


class SiteInline(admin.StackedInline):
    model = Site
    extra = 0


class ContactInline(admin.StackedInline):
    model = Contact
    extra = 0


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0
    fk_name = 'organization'
    autocomplete_fields = ['zip_code']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'trade_name', 'legal_name', 'organization_type', 'tax_id', 'is_active')
    list_filter = ('is_active', 'organization_type', 'created_at')
    search_fields = ('trade_name', 'legal_name', 'tax_id', 'primary_email')
    inlines = [SiteInline, ContactInline, AddressInline]


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'code', 'name', 'locale', 'is_active')
    list_filter = ('is_active', 'locale')
    search_fields = ('organization__trade_name', 'organization__legal_name', 'code', 'name')
    autocomplete_fields = ['organization']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'get_full_name', 'organization', 'site', 'role', 'department', 'status')
    list_filter = ('status', 'organization', 'department', 'created_at')
    search_fields = ('external_id', 'first_name', 'last_name', 'second_last_name', 'email', 'organization__trade_name')
    autocomplete_fields = ['organization', 'site']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'organization', 'site', 'role', 'email', 'is_primary')
    list_filter = ('is_primary', 'organization')
    search_fields = ('full_name', 'email', 'phone', 'organization__trade_name')
    autocomplete_fields = ['organization', 'site']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'organization', 'site', 'person', 'street', 'zip_code', 'city', 'region', 'country')
    list_filter = ('country', 'region')
    search_fields = ('street', 'city', 'region', 'country', 'organization__trade_name', 'person__first_name', 'person__last_name')
    autocomplete_fields = ['organization', 'site', 'person', 'zip_code']


@admin.register(ZipCode)
class ZipCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'zip_code', 'settlement', 'municipality', 'region', 'city', 'country')
    list_filter = ('country', 'region', 'city')
    search_fields = ('zip_code', 'settlement', 'normalized_settlement', 'municipality', 'region', 'city')


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'applies_to', 'is_required', 'default_validity_days')
    list_filter = ('applies_to', 'is_required')
    search_fields = ('code', 'name', 'description')


@admin.register(DocumentFile)
class DocumentFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'organization', 'site', 'person', 'status', 'expiration_date')
    list_filter = ('status', 'category', 'expiration_date')
    search_fields = ('title', 'category__name', 'organization__trade_name', 'person__first_name', 'person__last_name')
    autocomplete_fields = ['category', 'organization', 'site', 'person']


class DossierItemInline(admin.TabularInline):
    model = DossierItem
    extra = 0
    autocomplete_fields = ['category', 'document']


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'organization', 'site', 'person', 'status')
    list_filter = ('status', 'organization')
    search_fields = ('name', 'organization__trade_name', 'person__first_name', 'person__last_name')
    autocomplete_fields = ['organization', 'site', 'person']
    inlines = [DossierItemInline]


@admin.register(DossierItem)
class DossierItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'dossier', 'category', 'document', 'is_required', 'is_complete')
    list_filter = ('is_required', 'is_complete', 'category')
    autocomplete_fields = ['dossier', 'category', 'document']


class ProcessStepTemplateInline(admin.TabularInline):
    model = ProcessStepTemplate
    extra = 1
    autocomplete_fields = ['required_document_category']


@admin.register(ProcessTemplate)
class ProcessTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'description')
    inlines = [ProcessStepTemplateInline]


@admin.register(ProcessStepTemplate)
class ProcessStepTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'template', 'order', 'name', 'required_document_category', 'due_days')
    list_filter = ('template',)
    search_fields = ('name', 'template__name')
    autocomplete_fields = ['template', 'required_document_category']


class CaseStepInline(admin.TabularInline):
    model = CaseStep
    extra = 0
    autocomplete_fields = ['template_step']


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organization', 'person', 'template', 'status', 'due_date')
    list_filter = ('status', 'template', 'organization')
    search_fields = ('title', 'organization__trade_name', 'person__first_name', 'person__last_name')
    autocomplete_fields = ['template', 'organization', 'person']
    inlines = [CaseStepInline]


@admin.register(CaseStep)
class CaseStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'case', 'order', 'name', 'status', 'assigned_to', 'due_date')
    list_filter = ('status', 'due_date')
    search_fields = ('name', 'case__title', 'assigned_to')
    autocomplete_fields = ['case', 'template_step']


@admin.register(AuditNote)
class AuditNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organization', 'person', 'case', 'author', 'created_at')
    list_filter = ('organization', 'created_at')
    search_fields = ('title', 'body', 'author', 'organization__trade_name')
    autocomplete_fields = ['organization', 'person', 'case']


# Proxy that exposes /admin/data/customer/ for the iframe in
# templates/customer/customers.html. The class name becomes the model_name
# and therefore defines the admin URL segment. The class must be named
# 'Customer' so the URL remains /admin/data/customer/, not 'CustomerProxy',
# which would produce /admin/data/customerproxy/ and break the iframe with a 404.
class Customer(Organization):
    class Meta:
        proxy = True
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers (Organizations)'

@admin.register(Customer)
class CustomerAdmin(OrganizationAdmin):
    pass


# Proxy that exposes /admin/data/personal/ for the iframe in
# templates/personal/personal.html, used by /employees/ and /candidates/.
# The same rule applies: the class must be named 'Personal' so the URL remains
# /admin/data/personal/.
class Personal(Person):
    class Meta:
        proxy = True
        verbose_name = 'Personnel'
        verbose_name_plural = 'Personnel (People)'

@admin.register(Personal)
class PersonalAdmin(PersonAdmin):
    pass
