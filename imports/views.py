from django.http import FileResponse
import os
from django.conf import settings


# Create your views here.
def download_csv_template(request):
    """
    Handles the download of a CSV template file.

    This view function retrieves a CSV template file from the server's file system
    and returns it as a downloadable response to the client.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        FileResponse: A response object that allows the client to download the CSV file.
    """
    file_path = os.path.join(settings.MEDIA_ROOT, 'file_templates', 'imports_template.csv')
    response = FileResponse(open(file_path, 'rb'), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template.csv"'

    return response
