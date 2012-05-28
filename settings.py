# Django settings for gass project.
import os
from ConfigParser import RawConfigParser
config = RawConfigParser()
config.read('/etc/gass/settings.ini')

SETTINGS_ROOT = os.path.dirname(__file__)

DEBUG = config.getboolean('debug','DEBUG')
TEMPLATE_DEBUG = config.getboolean('debug','TEMPLATE_DEBUG')

ADMINS = (
    tuple(config.items('error mail'))
)

MANAGERS = tuple(config.items('404 mail'))

DEFAULT_DB_ALIAS = config.get('database', 'DATABASE_USER')

DATABASES = {
    'default': {
        'ENGINE':   'django.contrib.gis.db.backends.postgis', 
        'NAME':     config.get('database', 'DATABASE_NAME'),
        'USER':     config.get('database', 'DATABASE_USER'),
        'PASSWORD': config.get('database', 'DATABASE_PASSWORD'),
        'HOST':     config.get('database', 'DATABASE_HOST'),
        'PORT':     config.get('database', 'DATABASE_PORT'),
    }
}

CACHE_BACKEND = 'dummy:///'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = config.get('media','MEDIA_ROOT')

# location where Apache serves static files not specific to this project
APACHE_STATIC_ROOT = config.get('media','APACHE_STATIC_ROOT')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# SERVE STATIC FILES from the path to media files
# 'site_media' to STATIC_DOC_ROOT
STATIC_DOC_ROOT = config.get('media','STATIC_DOC_ROOT')

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'
STATIC_URL = '/admin_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('secrets','SECRET_KEY')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#   'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

ROOT_URLCONF = 'gass.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/usr/local/dev/gass/public/templates'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
#   'django.contrib.sites',
    'django.contrib.messages',
#   'django.contrib.gis',
    'django.contrib.admin',
    'gass.api',
    'gass.bering',
    'gass.public',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            #'filename':os.path.join(PARENT_DIR, 'django.log'),
            'filename': config.get('logging', 'ERROR_LOG_FILENAME'),
            'formatter': 'default'
        },
        'loading': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': config.get('logging', 'LOADING_LOG_FILENAME'),
            'formatter': 'default'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'error': {
            'handlers': ['error'],
            'level': 'ERROR',
            'propagate': False,
        },
        'loading': {
            'handlers': ['loading', 'error'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}
