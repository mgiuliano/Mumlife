import inspect
import os
import sys
import django.core.handlers.wsgi

SCRIPT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(ROOT_DIR)

# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
os.environ["DJANGO_SETTINGS_MODULE"] = "conf.settings"
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mumlife.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
