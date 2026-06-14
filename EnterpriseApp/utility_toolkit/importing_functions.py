import hashlib
from django.db import connections


def calculate_checksum(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        data = f.read()
        checksum = hashlib.sha256(data).hexdigest()
    return checksum


def calculate_checksum_sql(django_dbname: str, query) -> str:
    connection = connections[django_dbname]
    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchone()
        checksum = result[0] if result else None
    return checksum


def populate_database_if_data_row_is_none(model, model_fields_input, unique_identifier_field_name, database_objects, objects_to_create):
    # Check if the data already exists in the database
    if getattr(model_fields_input, unique_identifier_field_name) in database_objects:
        # Update existing object if data has changed
        existing_object = model.objects.get(**{unique_identifier_field_name: getattr(model_fields_input, unique_identifier_field_name)})
        for field in model._meta.get_fields():
            if field.name != 'id':
                if getattr(existing_object, field.name) != getattr(model_fields_input, field.name):
                    setattr(existing_object, field.name, getattr(model_fields_input, field.name))
                    existing_object.save()
                    break
    else:
        objects_to_create.append(model_fields_input)


def save_and_clear_data_row(model, objects, total_rows, i, stdout):
    if i % 1000 == 0 or i == total_rows - 1:
        model.objects.bulk_create(objects)
        objects.clear()
        stdout.write(f'Processed row {i + 1} of {total_rows}')
