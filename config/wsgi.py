"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys

# Add the project directory to the sys.path - flexible for both local and production
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Virtual environment activation - only for production deployment
if os.path.exists('/home/LearningManagementSystem/myenv/bin/activate_this.py'):
    activate_env = '/home/LearningManagementSystem/myenv/bin/activate_this.py'
    exec(open(activate_env).read(), {'__file__': activate_env})

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
