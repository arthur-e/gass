# WSGI configuration for running Django projects
# see: http://docs.djangoproject.com/en/dev/howto/deployment/modwsgi/

import os
import sys
import site

############################
# Virtual environment setup
ALLDIRS = ['/usr/local/pythonenv/django1.3-env/lib/python2.7/site-packages/']

# Remember original sys.path
prev_sys_path = list(sys.path)

# Add each new site-packages directory
for directory in ALLDIRS:
    site.addsitedir(directory)

# Reorder sys.path so new directories are at the front
new_sys_path = []
for item in list(sys.path): 
    if item not in prev_sys_path: 
        new_sys_path.append(item) 
        sys.path.remove(item) 
sys.path[:0] = new_sys_path

# End setup
############

# Add the path of the Django version
sys.path.append('/usr/local/django/trunk')

# Append the django project root directory to the python path
sys.path.append('/usr/local/project')
sys.path.append('/usr/local/project/gass')

os.environ['DJANGO_SETTINGS_MODULE'] = 'gass.settings'
os.environ['TEMPORARY_DIRECTORY'] = '/usr/local/project/gass/tmp'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
