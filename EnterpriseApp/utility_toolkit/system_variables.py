from EnterpriseApp.utility_toolkit.json_functions import JSONToolkit

importer = JSONToolkit()

choices_data = importer.import_choices('choices_variables', 'as_tuple')
DEPARTMENT_CHOICES = choices_data.get('DEPARTMENT_CHOICES', ())
LOCALES = choices_data.get('LOCALES', ())
ORGANIZATION_STATUS = choices_data.get('ORGANIZATION_STATUS', ())
PERSON_STATUS = choices_data.get('PERSON_STATUS', ())
DOCUMENT_STATUS = choices_data.get('DOCUMENT_STATUS', ())
PROCESS_STATUS = choices_data.get('PROCESS_STATUS', ())

settings_variables = importer.import_data('settings_variables')
REPORT_CONSTANTS = importer.import_data('report_variables')
