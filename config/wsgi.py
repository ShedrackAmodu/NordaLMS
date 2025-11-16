"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys

# Add the project directory to the sys.path
path = '/home/LearningManagementSystem/NordaLMS'
if path not in sys.path:
    sys.path.insert(0, '/home/LearningManagementSystem/NordaLMS')

# Activate virtualenv
activate_env=os.path.expanduser('/home/LearningManagementSystem/myenv/bin/activate_this.py')
exec(open(activate_env).read(), {'__file__': activate_env})

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
