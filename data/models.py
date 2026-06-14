"""Generic domain models for the public Enterprise DMS version.

This module intentionally removes company-specific private concepts such as
customer-specific evaluations, regulated-industry checks, biometric fields,
license-oriented reports, and similar private workflow details.

The goal is to keep the reusable product idea: organizations, people,
locations, documents, dossiers, workflows, reminders and import metadata.
"""

from __future__ import annotations

import logging
from datetime import date

from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from unidecode import unidecode

from EnterpriseApp.utility_toolkit.uploading_functions import set_upload_path

logger = logging.getLogger(__name__)

PHONE_VALIDATOR = RegexValidator(
    regex=r"^\+?\d[\d\s().-]{6,30}$",
    message='Enter a valid phone number. It may include an international prefix, spaces, periods, or hyphens.',
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='updated')

    class Meta:
        abstract = True


class ZipCode(TimeStampedModel):
    """Postal/geographic catalog.

    Field names keep compatibility with the previous importer, but the model is
    generic and can hold postal data from any country.
    """

    zip_code = models.CharField(max_length=12, default='', blank=True, db_index=True, verbose_name='zip code')
    settlement_type = models.CharField(max_length=80, default='', blank=True, verbose_name='settlement type')
    settlement = models.CharField(max_length=200, default='', blank=True, verbose_name='settlement')
    normalized_settlement = models.CharField(max_length=255, default='', blank=True, db_index=True, verbose_name='normalized settlement')
    municipality = models.CharField(max_length=120, default='', blank=True, verbose_name='municipality / county')
    region = models.CharField(max_length=120, default='', blank=True, verbose_name='state / region')
    city = models.CharField(max_length=120, default='', blank=True, verbose_name='city')
    country = models.CharField(max_length=80, default='Mexico', blank=True, db_index=True, verbose_name='country')

    @property
    def state(self):
        return self.region

    def __str__(self):
        location = ', '.join(part for part in [self.settlement, self.city, self.region, self.country] if part)
        return f'{self.zip_code}: {location}' if location else self.zip_code

    def save(self, *args, **kwargs):
        for field in ('settlement_type', 'settlement', 'municipality', 'region', 'city', 'country'):
            value = getattr(self, field, '') or ''
            setattr(self, field, str(value).strip().title())
        self.zip_code = str(self.zip_code or '').strip()
        self.normalized_settlement = unidecode(self.settlement or '').upper()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Zip code'
        verbose_name_plural = 'Zip codes'
        indexes = [
            models.Index(fields=['zip_code', 'normalized_settlement'], name='zipcode_search_idx'),
            models.Index(fields=['country', 'region', 'city'], name='zipcode_location_idx'),
        ]


class Organization(TimeStampedModel):
    """Any client/company/institution managed by the system."""

    legal_name = models.CharField(max_length=220, verbose_name='legal name')
    trade_name = models.CharField(max_length=220, default='', blank=True, db_index=True, verbose_name='trade name')
    organization_type = models.CharField(max_length=80, default='', blank=True, verbose_name='organization type')
    tax_id = models.CharField(max_length=50, default='', blank=True, db_index=True, verbose_name='tax identifier')
    website = models.URLField(default='', blank=True, verbose_name='website')
    primary_email = models.EmailField(default='', blank=True, verbose_name='primary email')
    primary_phone = models.CharField(max_length=35, default='', blank=True, validators=[PHONE_VALIDATOR], verbose_name='primary phone')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='active')
    notes = models.TextField(default='', blank=True, verbose_name='notes')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    @property
    def business_name(self):
        # Compatibility alias for old documentation/examples.
        return self.trade_name or self.legal_name

    @property
    def registered_name(self):
        return self.legal_name

    def __str__(self):
        return self.trade_name or self.legal_name

    def save(self, *args, **kwargs):
        self.legal_name = str(self.legal_name or '').strip().title()
        self.trade_name = str(self.trade_name or '').strip().title()
        self.tax_id = str(self.tax_id or '').strip().upper()
        self.primary_email = str(self.primary_email or '').strip().lower()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        ordering = ['trade_name', 'legal_name']


class Site(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='sites', verbose_name='organization')
    code = models.CharField(max_length=30, default='', blank=True, db_index=True, verbose_name='code')
    name = models.CharField(max_length=180, verbose_name='name')
    description = models.TextField(default='', blank=True, verbose_name='description')
    locale = models.CharField(max_length=8, default='mx', blank=True, verbose_name='locale')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='active')

    def __str__(self):
        return f'{self.organization} / {self.name}'

    def save(self, *args, **kwargs):
        self.code = str(self.code or '').strip().upper()
        self.name = str(self.name or '').strip().title()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Site'
        verbose_name_plural = 'Sites'
        unique_together = ('organization', 'code')
        ordering = ['organization', 'name']


class Person(TimeStampedModel):
    STATUS_ACTIVE = 'active'
    STATUS_CANDIDATE = 'candidate'
    STATUS_INACTIVE = 'inactive'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CANDIDATE, 'Candidate / prospect'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='people', verbose_name='organization')
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name='people', verbose_name='site')
    external_id = models.CharField(max_length=80, default='', blank=True, db_index=True, verbose_name='external id')
    first_name = models.CharField(max_length=120, verbose_name='name')
    last_name = models.CharField(max_length=120, default='', blank=True, verbose_name='last name')
    second_last_name = models.CharField(max_length=120, default='', blank=True, verbose_name='second last name')
    email = models.EmailField(default='', blank=True, db_index=True, verbose_name='email')
    phone = models.CharField(max_length=35, default='', blank=True, validators=[PHONE_VALIDATOR], verbose_name='phone')
    role = models.CharField(max_length=120, default='', blank=True, verbose_name='position / role')
    department = models.CharField(max_length=120, default='', blank=True, verbose_name='department')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True, verbose_name='status')
    start_date = models.DateField(null=True, blank=True, verbose_name='start date')
    end_date = models.DateField(null=True, blank=True, verbose_name='end date')
    notes = models.TextField(default='', blank=True, verbose_name='notes')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    def __str__(self):
        return self.get_full_name() or self.external_id or f'Person #{self.pk or "new"}'

    def get_full_name(self):
        return ' '.join(part for part in [self.first_name, self.last_name, self.second_last_name] if part).strip()

    def save(self, *args, **kwargs):
        self.first_name = str(self.first_name or '').strip().title()
        self.last_name = str(self.last_name or '').strip().title()
        self.second_last_name = str(self.second_last_name or '').strip().title()
        self.email = str(self.email or '').strip().lower()
        self.external_id = str(self.external_id or '').strip().upper()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'People'
        ordering = ['organization', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['organization', 'status'], name='person_org_status_idx'),
            models.Index(fields=['external_id'], name='person_external_id_idx'),
        ]


class Contact(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='contacts', verbose_name='organization')
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts', verbose_name='site')
    full_name = models.CharField(max_length=220, verbose_name='name complete')
    role = models.CharField(max_length=120, default='', blank=True, verbose_name='position / role')
    email = models.EmailField(default='', blank=True, verbose_name='email')
    phone = models.CharField(max_length=35, default='', blank=True, validators=[PHONE_VALIDATOR], verbose_name='phone')
    is_primary = models.BooleanField(default=False, db_index=True, verbose_name='primary contact')
    notes = models.TextField(default='', blank=True, verbose_name='notes')

    def __str__(self):
        return f'{self.full_name} - {self.organization}'

    def save(self, *args, **kwargs):
        self.full_name = str(self.full_name or '').strip().title()
        self.email = str(self.email or '').strip().lower()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['organization', '-is_primary', 'full_name']


class Address(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='addresses', verbose_name='organization')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True, related_name='addresses', verbose_name='site')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True, related_name='addresses', verbose_name='person')
    label = models.CharField(max_length=80, default='primary', blank=True, verbose_name='label')
    street = models.CharField(max_length=220, default='', blank=True, verbose_name='street')
    exterior_number = models.CharField(max_length=40, default='', blank=True, verbose_name='exterior number')
    interior_number = models.CharField(max_length=40, default='', blank=True, verbose_name='interior number')
    zip_code = models.ForeignKey(ZipCode, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='zip code')
    city = models.CharField(max_length=120, default='', blank=True, verbose_name='city')
    region = models.CharField(max_length=120, default='', blank=True, verbose_name='state / region')
    country = models.CharField(max_length=80, default='Mexico', blank=True, verbose_name='country')
    notes = models.TextField(default='', blank=True, verbose_name='notes')

    def __str__(self):
        parts = [self.street, self.exterior_number, self.interior_number]
        return ' '.join(part for part in parts if part) or f'Address #{self.pk or "new"}'

    def save(self, *args, **kwargs):
        if self.zip_code:
            self.city = self.city or self.zip_code.city
            self.region = self.region or self.zip_code.region
            self.country = self.country or self.zip_code.country
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'


class DocumentCategory(TimeStampedModel):
    APPLIES_GENERAL = 'general'
    APPLIES_ORGANIZATION = 'organization'
    APPLIES_SITE = 'site'
    APPLIES_PERSON = 'person'

    APPLIES_TO_CHOICES = [
        (APPLIES_GENERAL, 'General'),
        (APPLIES_ORGANIZATION, 'Organization'),
        (APPLIES_SITE, 'Site'),
        (APPLIES_PERSON, 'Person'),
    ]

    code = models.CharField(max_length=80, unique=True, verbose_name='code')
    name = models.CharField(max_length=180, verbose_name='name')
    applies_to = models.CharField(max_length=30, choices=APPLIES_TO_CHOICES, default=APPLIES_GENERAL, db_index=True, verbose_name='applies to')
    description = models.TextField(default='', blank=True, verbose_name='description')
    is_required = models.BooleanField(default=False, db_index=True, verbose_name='required')
    default_validity_days = models.PositiveIntegerField(null=True, blank=True, verbose_name='default validity in days')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.code = str(self.code or '').strip().upper().replace(' ', '_')
        self.name = str(self.name or '').strip().title()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Document category'
        verbose_name_plural = 'Document categories'
        ordering = ['applies_to', 'name']


class DocumentFile(TimeStampedModel):
    STATUS_PENDING = 'pending'
    STATUS_CURRENT = 'current'
    STATUS_EXPIRED = 'expired'
    STATUS_REJECTED = 'rejected'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CURRENT, 'Current'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT, related_name='documents', verbose_name='category')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='documents', verbose_name='organization')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True, related_name='documents', verbose_name='site')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True, related_name='documents', verbose_name='person')
    title = models.CharField(max_length=220, default='', blank=True, verbose_name='title')
    file = models.FileField(upload_to=set_upload_path, validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'csv'])], verbose_name='file')
    issue_date = models.DateField(null=True, blank=True, verbose_name='issue date')
    expiration_date = models.DateField(null=True, blank=True, db_index=True, verbose_name='expiration date')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True, verbose_name='status')
    checksum = models.CharField(max_length=128, default='', blank=True, db_index=True, verbose_name='checksum')
    notes = models.TextField(default='', blank=True, verbose_name='notes')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    def __str__(self):
        return self.title or f'{self.category} #{self.pk or "new"}'

    @property
    def is_expired(self):
        return bool(self.expiration_date and self.expiration_date < date.today())

    def save(self, *args, **kwargs):
        if not self.title and self.category_id:
            self.title = str(self.category)
        if self.is_expired:
            self.status = self.STATUS_EXPIRED
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['expiration_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'expiration_date'], name='document_status_exp_idx'),
        ]


class Dossier(TimeStampedModel):
    STATUS_OPEN = 'open'
    STATUS_IN_REVIEW = 'in_review'
    STATUS_COMPLETE = 'complete'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_REVIEW, 'In review'),
        (STATUS_COMPLETE, 'Complete'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='dossiers', verbose_name='organization')
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name='dossiers', verbose_name='site')
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='dossiers', verbose_name='person')
    name = models.CharField(max_length=220, verbose_name='name')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True, verbose_name='status')
    description = models.TextField(default='', blank=True, verbose_name='description')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Dossier'
        verbose_name_plural = 'Dossiers'
        ordering = ['organization', 'name']


class DossierItem(TimeStampedModel):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='items', verbose_name='dossier')
    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT, related_name='dossier_items', verbose_name='category')
    document = models.ForeignKey(DocumentFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='dossier_items', verbose_name='document')
    is_required = models.BooleanField(default=True, db_index=True, verbose_name='required')
    is_complete = models.BooleanField(default=False, db_index=True, verbose_name='complete')
    notes = models.TextField(default='', blank=True, verbose_name='notes')

    def __str__(self):
        return f'{self.dossier} / {self.category}'

    class Meta:
        verbose_name = 'Dossier item'
        verbose_name_plural = 'Dossier items'
        unique_together = ('dossier', 'category')


class ProcessTemplate(TimeStampedModel):
    code = models.CharField(max_length=80, unique=True, verbose_name='code')
    name = models.CharField(max_length=180, verbose_name='name')
    description = models.TextField(default='', blank=True, verbose_name='description')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='active')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.code = str(self.code or '').strip().upper().replace(' ', '_')
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Process template'
        verbose_name_plural = 'Process templates'


class ProcessStepTemplate(TimeStampedModel):
    template = models.ForeignKey(ProcessTemplate, on_delete=models.CASCADE, related_name='steps', verbose_name='template')
    name = models.CharField(max_length=180, verbose_name='name')
    order = models.PositiveIntegerField(default=1, db_index=True, verbose_name='order')
    required_document_category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='document required')
    due_days = models.PositiveIntegerField(null=True, blank=True, verbose_name='due days')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    def __str__(self):
        return f'{self.template} / {self.order}. {self.name}'

    class Meta:
        verbose_name = 'Template step'
        verbose_name_plural = 'Template steps'
        ordering = ['template', 'order']
        unique_together = ('template', 'order')


class Case(TimeStampedModel):
    STATUS_OPEN = 'open'
    STATUS_BLOCKED = 'blocked'
    STATUS_COMPLETE = 'complete'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_BLOCKED, 'Bloqueado'),
        (STATUS_COMPLETE, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    template = models.ForeignKey(ProcessTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='cases', verbose_name='template')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='cases', verbose_name='organization')
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='cases', verbose_name='person')
    title = models.CharField(max_length=220, verbose_name='title')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True, verbose_name='status')
    opened_at = models.DateField(auto_now_add=True, verbose_name='opened at')
    due_date = models.DateField(null=True, blank=True, db_index=True, verbose_name='due date')
    closed_at = models.DateField(null=True, blank=True, verbose_name='closed at')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Case / process'
        verbose_name_plural = 'Cases / processes'
        ordering = ['due_date', '-created_at']


class CaseStep(TimeStampedModel):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'
    STATUS_SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In progress'),
        (STATUS_DONE, 'Completed'),
        (STATUS_SKIPPED, 'Skipped'),
    ]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='steps', verbose_name='case')
    template_step = models.ForeignKey(ProcessStepTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='template step')
    name = models.CharField(max_length=180, verbose_name='name')
    order = models.PositiveIntegerField(default=1, db_index=True, verbose_name='order')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True, verbose_name='status')
    assigned_to = models.CharField(max_length=180, default='', blank=True, verbose_name='assigned to')
    due_date = models.DateField(null=True, blank=True, verbose_name='due date')
    completed_at = models.DateField(null=True, blank=True, verbose_name='completion date')
    notes = models.TextField(default='', blank=True, verbose_name='notes')

    def __str__(self):
        return f'{self.case} / {self.order}. {self.name}'

    class Meta:
        verbose_name = 'Case step'
        verbose_name_plural = 'Case steps'
        ordering = ['case', 'order']


class AuditNote(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_notes', verbose_name='organization')
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_notes', verbose_name='person')
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_notes', verbose_name='case')
    title = models.CharField(max_length=180, verbose_name='title')
    body = models.TextField(default='', blank=True, verbose_name='details')
    author = models.CharField(max_length=180, default='', blank=True, verbose_name='author')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='metadata')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Audit note'
        verbose_name_plural = 'Audit notes'
        ordering = ['-created_at']


# Compatibility aliases for older docs/scripts. They point to generic models and
# do not reintroduce the private domain schema.
Customer = Organization
Location = Site
Personl = Person
