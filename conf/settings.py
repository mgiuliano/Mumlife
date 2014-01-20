# Local Settings
import inspect
import os
import stat
from common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Beatscope Engineering', 'support@beatscope.co.uk'),
)
MANAGERS = ADMINS

EMAIL_FROM = 'support@beatscope.co.uk'
EMAIL_SUBJECT_PREFIX = '[Mumlife] '
SERVER_EMAIL = 'support@beatscope.co.uk'
EMAIL_FROM = 'Mumlife <support@beatscope.co.uk>'

# dumb SMTP server
# python -m smtpd -n -c DebuggingServer localhost:1025
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

SITE_URL = 'http://mumlife.bsc-dev.com/'
API_URL = 'http://mumlife.bsc-dev.com/1/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mumlife',
        'USER': 'mumlife_dba',
        'PASSWORD': 'pass',
        'HOST': 'localhost',
        'PORT': '',
    }
}


ALLOWED_HOSTS = ['*']

MEDIA_ROOT = '/home/michael/projects/mumlife/uploads'
MEDIA_URL = 'http://mumlife.bsc-dev.com/media/'
STATIC_ROOT = '/home/michael/projects/mumlife/static'
STATIC_URL = 'http://mumlife.bsc-dev.com/static/'

STATICFILES_DIRS = (
    '/home/michael/projects/mumlife/mumlife/static',
)

SECRET_KEY = 'fxua&#*47eu5m!rtc5cirp00y^7oroihbd@o^3j38e96lg4p&y'

TEMPLATE_DIRS = (
    '/home/michael/projects/mumlife/mumlife/templates',
)

### LOGGING
SCRIPT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
LOGFILENAME = os.path.abspath(os.path.join(SCRIPT_DIR, '../../runtime/runtime.log'))
LOGFILE = open(LOGFILENAME, 'a+')
try:
    # The file owner sets the permissions to 777 so every process can log to the same file
    os.chmod(LOGFILE.name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
except OSError:
    pass
LOGGING['formatters'] = {
    'verbose': {
        'format': '[%(levelname)s] %(asctime)s %(module)s: %(message)s'
    }
}
LOGGING['handlers']['log_to_file'] = {
    'class': 'logging.FileHandler',
    'filename': LOGFILE.name,
    'formatter': 'verbose',
}
LOGGING['loggers']['mumlife'] = {
    'handlers': ['log_to_file'],
    'level': 'DEBUG',
    'propagate': True,
}
