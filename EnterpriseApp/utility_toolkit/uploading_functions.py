import os
from uuid import uuid4


def set_upload_path(instance, filename):
    """Return a generic, privacy-safe upload path for attached files.

    The path is intentionally based on generic relations such as organization,
    person or site. It avoids embedding private business categories in the file
    structure.
    """
    _, ext = os.path.splitext(filename)
    unique_filename = f"{uuid4().hex}{ext}"

    organization = getattr(instance, 'organization', None)
    person = getattr(instance, 'person', None)
    site = getattr(instance, 'site', None)

    if person is not None:
        organization = organization or getattr(person, 'organization', None)
        person_label = getattr(person, 'external_id', None) or str(getattr(person, 'id', 'person'))
        organization_label = getattr(organization, 'trade_name', None) or 'organization'
        directory = os.path.join('Documents', str(organization_label), 'people', str(person_label))
    elif site is not None:
        organization = organization or getattr(site, 'organization', None)
        site_label = getattr(site, 'code', None) or str(getattr(site, 'id', 'site'))
        organization_label = getattr(organization, 'trade_name', None) or 'organization'
        directory = os.path.join('Documents', str(organization_label), 'sites', str(site_label))
    elif organization is not None:
        organization_label = getattr(organization, 'trade_name', None) or str(getattr(organization, 'id', 'organization'))
        directory = os.path.join('Documents', str(organization_label), 'general')
    else:
        directory = os.path.join('Documents', 'unclassified')

    return os.path.join(directory, unique_filename)
