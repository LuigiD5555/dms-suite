"""Generic CSV importer for the public Enterprise DMS schema.

CSV headers must use Model_field format, for example:

Organization_trade_name,Organization_legal_name,Person_first_name,Person_last_name,Person_email
Acme,Acme S.A.,Ana,Perez,ana@example.com

Supported model prefixes:
Organization, Site, Person, Contact, Address, DocumentCategory, Dossier,
ProcessTemplate, Case.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import pandas as pd
from dateutil import parser
from django.db import transaction
from django.db.models import Model
from unidecode import unidecode

from data.models import (
    Address,
    AuditNote,
    Case,
    Contact,
    DocumentCategory,
    Dossier,
    Organization,
    Person,
    ProcessTemplate,
    Site,
    ZipCode,
)

logger = logging.getLogger(__name__)


class CSVImporter:
    SUPPORTED_ENCODINGS = ('utf-8-sig', 'utf-8', 'latin-1')
    WORDS_TO_DELETE = ['COLONIA', 'COL.', 'FRACCIONAMIENTO', 'FRACC.', 'BARRIO', 'EJIDO']

    MODEL_MAP: dict[str, type[Model]] = {
        'Organization': Organization,
        'Customer': Organization,  # compatibility alias
        'Site': Site,
        'Location': Site,  # compatibility alias
        'Person': Person,
        'Personal': Person,  # compatibility alias
        'Contact': Contact,
        'Address': Address,
        'ZipCode': ZipCode,
        'DocumentCategory': DocumentCategory,
        'Dossier': Dossier,
        'ProcessTemplate': ProcessTemplate,
        'Case': Case,
        'AuditNote': AuditNote,
    }

    def __init__(self, csv_file_path: str, import_log=None):
        self.csv_file_path = csv_file_path
        self.import_log = import_log
        self.rows_processed = 0
        self.rows_success = 0
        self.errors: list[dict[str, Any]] = []

    def import_data_from_csv(self) -> dict[str, Any]:
        self._validate_csv_file()
        df = self._read_csv()
        self._validate_headers(df.columns.tolist())
        for index, row in df.iterrows():
            row_number = int(index) + 2
            self._store_import_row(row_number, row.to_dict())
            self.rows_processed += 1
            try:
                with transaction.atomic():
                    self._process_row(row)
                self.rows_success += 1
                self._mark_import_row(row_number, 'ok')
            except Exception as exc:  # noqa: BLE001 - import UI needs row-level details
                logger.exception('Error importing row %s', row_number)
                error = {'row': row_number, 'error': str(exc)}
                self.errors.append(error)
                self._mark_import_row(row_number, 'error', str(exc))
        return {
            'processed': self.rows_processed,
            'success': self.rows_success,
            'errors': len(self.errors),
            'error_detail': self.errors,
        }

    def _validate_csv_file(self):
        if not self.csv_file_path or not os.path.exists(self.csv_file_path):
            raise FileNotFoundError(f'CSV file does not exist: {self.csv_file_path}')
        if not self.csv_file_path.lower().endswith('.csv'):
            raise ValueError('The file must have a .csv extension')
        if os.path.getsize(self.csv_file_path) == 0:
            raise ValueError('The CSV file is empty')

    def _read_csv(self) -> pd.DataFrame:
        last_error = None
        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                return pd.read_csv(self.csv_file_path, dtype=str, encoding=encoding)
            except UnicodeDecodeError as exc:
                last_error = exc
        raise ValueError(f'The CSV could not be read with a supported encoding: {last_error}')

    def _validate_headers(self, headers: list[str]):
        invalid = [header for header in headers if '_' not in header]
        if invalid:
            raise ValueError(f'Invalid headers. They must use Model_field: {invalid[:10]}')
        unsupported = sorted({header.split('_', 1)[0] for header in headers if header.split('_', 1)[0] not in self.MODEL_MAP})
        if unsupported:
            raise ValueError(f'Unsupported CSV models: {unsupported}')

    def _process_row(self, row: pd.Series):
        grouped = self._group_row_data(row)
        organization = self._upsert_organization(grouped)
        site = self._upsert_site(grouped, organization)
        person = self._upsert_person(grouped, organization, site)
        self._upsert_contact(grouped, organization, site)
        self._upsert_address(grouped, organization, site, person)
        self._upsert_document_category(grouped)
        self._upsert_dossier(grouped, organization, site, person)
        self._upsert_process_template(grouped)
        self._upsert_case(grouped, organization, person)
        self._upsert_audit_note(grouped, organization, person)

    def _group_row_data(self, row: pd.Series) -> dict[str, dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for header, value in row.to_dict().items():
            if pd.isnull(value):
                continue
            model_name, field_name = header.split('_', 1)
            canonical = self._canonical_model_name(model_name)
            grouped.setdefault(canonical, {})[field_name.lower()] = self._normalize_value(field_name.lower(), value)
        return grouped

    def _canonical_model_name(self, model_name: str) -> str:
        aliases = {'Customer': 'Organization', 'Location': 'Site', 'Personal': 'Person'}
        return aliases.get(model_name, model_name)

    def _normalize_value(self, field_name: str, value: Any) -> Any:
        text = str(value).strip()
        if not text:
            return ''
        if field_name.endswith('_date') or field_name in {'start_date', 'end_date', 'due_date', 'closed_at', 'opened_at'}:
            try:
                return parser.parse(text, dayfirst=True).date()
            except (ValueError, TypeError):
                return text
        if field_name in {'is_active', 'is_primary', 'is_required', 'is_complete'}:
            return text.lower() in {'1', 'true', 'yes', 'si', 'sí', 'y'}
        return text

    def _upsert_organization(self, grouped: dict[str, dict[str, Any]]) -> Organization:
        data = grouped.get('Organization', {})
        if not data:
            raise ValueError('The row must contain Organization_legal_name u Organization_trade_name')
        legal_name = data.get('legal_name') or data.get('registered_name') or data.get('trade_name') or data.get('business_name')
        trade_name = data.get('trade_name') or data.get('business_name') or legal_name
        if not legal_name:
            raise ValueError('The organization has no legal or trade name')
        data['legal_name'] = legal_name
        data['trade_name'] = trade_name
        return self._safe_update_or_create(Organization, data, ['tax_id'], fallback_lookup=['trade_name'])

    def _upsert_site(self, grouped: dict[str, dict[str, Any]], organization: Organization) -> Site | None:
        data = grouped.get('Site', {})
        if not data:
            return None
        data['organization'] = organization
        data['name'] = data.get('name') or data.get('location_name') or data.get('code') or 'Principal'
        data['code'] = data.get('code') or data.get('location_key') or data['name'][:20]
        return self._safe_update_or_create(Site, data, ['organization', 'code'], fallback_lookup=['organization', 'name'])

    def _upsert_person(self, grouped: dict[str, dict[str, Any]], organization: Organization, site: Site | None) -> Person | None:
        data = grouped.get('Person', {})
        if not data:
            return None
        data['organization'] = organization
        if site:
            data.setdefault('site', site)
        data['first_name'] = data.get('first_name') or data.get('nombre') or 'Unnamed'
        data['last_name'] = data.get('last_name') or data.get('apellido_paterno') or ''
        data['second_last_name'] = data.get('second_last_name') or data.get('apellido_materno') or ''
        lookup = ['organization', 'external_id'] if data.get('external_id') else ['organization', 'first_name', 'last_name', 'second_last_name']
        return self._safe_update_or_create(Person, data, lookup)

    def _upsert_contact(self, grouped: dict[str, dict[str, Any]], organization: Organization, site: Site | None) -> Contact | None:
        data = grouped.get('Contact', {})
        if not data:
            return None
        data['organization'] = organization
        if site:
            data.setdefault('site', site)
        data['full_name'] = data.get('full_name') or data.get('name') or data.get('nombre_contacto')
        if not data.get('full_name'):
            return None
        return self._safe_update_or_create(Contact, data, ['organization', 'email'], fallback_lookup=['organization', 'full_name'])

    def _upsert_address(self, grouped: dict[str, dict[str, Any]], organization: Organization, site: Site | None, person: Person | None) -> Address | None:
        data = grouped.get('Address', {})
        if not data:
            return None
        data['organization'] = organization
        if site:
            data.setdefault('site', site)
        if person:
            data.setdefault('person', person)
        zip_object = self._resolve_zip_code(data)
        if zip_object:
            data['zip_code'] = zip_object
        data['street'] = data.get('street') or data.get('calle') or ''
        return self._safe_update_or_create(Address, data, ['organization', 'site', 'person', 'label'], fallback_lookup=['organization', 'street'])

    def _upsert_document_category(self, grouped: dict[str, dict[str, Any]]) -> DocumentCategory | None:
        data = grouped.get('DocumentCategory', {})
        if not data:
            return None
        data['code'] = data.get('code') or data.get('name')
        data['name'] = data.get('name') or data['code']
        return self._safe_update_or_create(DocumentCategory, data, ['code'])

    def _upsert_dossier(self, grouped: dict[str, dict[str, Any]], organization: Organization, site: Site | None, person: Person | None) -> Dossier | None:
        data = grouped.get('Dossier', {})
        if not data:
            return None
        data['organization'] = organization
        if site:
            data.setdefault('site', site)
        if person:
            data.setdefault('person', person)
        data['name'] = data.get('name') or 'General dossier'
        return self._safe_update_or_create(Dossier, data, ['organization', 'person', 'name'])

    def _upsert_process_template(self, grouped: dict[str, dict[str, Any]]) -> ProcessTemplate | None:
        data = grouped.get('ProcessTemplate', {})
        if not data:
            return None
        data['code'] = data.get('code') or data.get('name')
        data['name'] = data.get('name') or data['code']
        return self._safe_update_or_create(ProcessTemplate, data, ['code'])

    def _upsert_case(self, grouped: dict[str, dict[str, Any]], organization: Organization, person: Person | None) -> Case | None:
        data = grouped.get('Case', {})
        if not data:
            return None
        data['organization'] = organization
        if person:
            data.setdefault('person', person)
        data['title'] = data.get('title') or 'General case'
        return self._safe_update_or_create(Case, data, ['organization', 'person', 'title'])

    def _upsert_audit_note(self, grouped: dict[str, dict[str, Any]], organization: Organization, person: Person | None) -> AuditNote | None:
        data = grouped.get('AuditNote', {})
        if not data:
            return None
        data['organization'] = organization
        if person:
            data.setdefault('person', person)
        data['title'] = data.get('title') or 'Note'
        return AuditNote.objects.create(**self._filter_model_fields(AuditNote, data))

    def _resolve_zip_code(self, data: dict[str, Any]) -> ZipCode | None:
        zip_value = data.pop('zip_code', None) or data.pop('codigo_postal', None)
        if isinstance(zip_value, ZipCode):
            return zip_value
        if not zip_value:
            return None
        query = ZipCode.objects.filter(zip_code=str(zip_value).strip().zfill(5))
        settlement = data.pop('settlement', None) or data.pop('asentamiento', None)
        if settlement:
            normalized = self._normalize_settlement(settlement)
            return query.filter(normalized_settlement__icontains=normalized).first() or query.first()
        return query.first()

    def _normalize_settlement(self, text: str) -> str:
        result = unidecode(str(text).strip()).upper()
        pattern = r'\b(?:' + '|'.join(re.escape(word) for word in self.WORDS_TO_DELETE) + r')\b'
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', result).strip()

    def _safe_update_or_create(self, model: type[Model], data: dict[str, Any], lookup_fields: list[str], fallback_lookup: list[str] | None = None):
        clean_data = self._filter_model_fields(model, data)
        lookup = {field: clean_data.get(field) for field in lookup_fields if clean_data.get(field) not in [None, '']}
        if len(lookup) != len(lookup_fields) and fallback_lookup:
            lookup = {field: clean_data.get(field) for field in fallback_lookup if clean_data.get(field) not in [None, '']}
        if not lookup:
            return model.objects.create(**clean_data)
        defaults = {key: value for key, value in clean_data.items() if key not in lookup}
        obj, _ = model.objects.update_or_create(defaults=defaults, **lookup)
        return obj

    @staticmethod
    def _filter_model_fields(model: type[Model], data: dict[str, Any]) -> dict[str, Any]:
        valid_fields = {field.name for field in model._meta.fields if not getattr(field, 'auto_created', False)}
        return {key: value for key, value in data.items() if key in valid_fields}

    def _store_import_row(self, row_number: int, raw_data: dict[str, Any]):
        if not self.import_log:
            return
        try:
            from imports.models import ImportRow
            ImportRow.objects.update_or_create(
                import_log=self.import_log,
                row_number=row_number,
                defaults={'raw_data': {k: '' if pd.isnull(v) else str(v) for k, v in raw_data.items()}},
            )
        except Exception:
            logger.exception('Could not save imported row details')

    def _mark_import_row(self, row_number: int, status: str, error_detail: str = ''):
        if not self.import_log:
            return
        try:
            from imports.models import ImportRow
            ImportRow.objects.filter(import_log=self.import_log, row_number=row_number).update(status=status, error_detail=error_detail)
        except Exception:
            logger.exception('Could not update imported row details')
