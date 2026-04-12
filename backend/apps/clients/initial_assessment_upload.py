"""Upload path helpers for initial assessment documents (storage-backend agnostic)."""
import os
import uuid

from django.utils.text import get_valid_filename


def initial_assessment_document_upload_to(instance, filename):
    """Store under initial_assessments/client_<id>/ to ease future blob prefix migration."""
    base = get_valid_filename(os.path.basename(filename)) if filename else 'document'
    if not base:
        base = 'document'
    safe = f'{uuid.uuid4().hex}_{base}'
    return f'initial_assessments/client_{instance.client_id}/{safe}'
