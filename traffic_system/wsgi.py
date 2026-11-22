"""
WSGI config for traffic_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traffic_system.settings')

application = get_wsgi_application()
app = application

# Auto-initialize database on Vercel serverless environment
if os.environ.get('VERCEL'):
    try:
        from django.core.management import call_command
        call_command('migrate', interactive=False)
        call_command('seed_data')
    except Exception:
        pass
