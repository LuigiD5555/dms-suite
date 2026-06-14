"""Configuration-driven reports for the public generic model."""

REPORT_TEMPLATES = {
    'organization_summary': {
        'model': 'data.Organization',
        'request_field': 'object_id',
        'lookup_field': 'id',
        'template_path': 'reports/templates/organization_summary.docx',
        'variables': {
            'legal_name': 'legal_name',
            'trade_name': 'trade_name',
            'organization_type': 'organization_type',
            'tax_id': 'tax_id',
            'primary_email': 'primary_email',
            'primary_phone': 'primary_phone',
            'is_active': 'is_active',
        },
        'output_format': 'docx',
        'description': 'General organization profile.',
    },
    'person_summary': {
        'model': 'data.Person',
        'request_field': 'object_id',
        'lookup_field': 'id',
        'template_path': 'reports/templates/person_summary.docx',
        'variables': {
            'external_id': 'external_id',
            'full_name': 'get_full_name',
            'email': 'email',
            'phone': 'phone',
            'role': 'role',
            'department': 'department',
            'status': 'status',
            'start_date': 'start_date',
            'organization': 'organization',
        },
        'output_format': 'docx',
        'description': 'General person/staff profile.',
    },
    'dossier_checklist': {
        'model': 'data.Dossier',
        'request_field': 'object_id',
        'lookup_field': 'id',
        'template_path': 'reports/templates/dossier_checklist.docx',
        'variables': {
            'name': 'name',
            'status': 'status',
            'description': 'description',
            'organization': 'organization',
            'person': 'person',
        },
        'output_format': 'docx',
        'description': 'Dossier document checklist.',
    },
}


def get_report_template(report_type: str) -> dict:
    if report_type not in REPORT_TEMPLATES:
        raise ValueError(f'Report type is not configured: {report_type}')
    return REPORT_TEMPLATES[report_type]
