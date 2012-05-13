# WSGI configuration for running Django projects
# see: http://docs.djangoproject.com/en/dev/howto/deployment/modwsgi/

import os
import sys

# Add the path of the Django version
sys.path.append('/usr/local/django/Django-1.3.1')

# Append the django project root directory to the python path
sys.path.append('/usr/local/dev')
sys.path.append('/usr/local/dev/gass')

os.environ['DJANGO_SETTINGS_MODULE'] = 'gass.settings'
os.environ['TEMPORARY_DIRECTORY'] = '/usr/local/dev/gass/tmp'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
