import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'gestion_papier_scolarite.settings')

application = get_wsgi_application()
