"""Isolated regression settings: never use the application's database."""
from .settings import *  # noqa: F401,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
# Legacy apps have incomplete migrations; build their current model schema in memory.
MIGRATION_MODULES = {app.split('.')[0]: None for app in INSTALLED_APPS
                     if not app.startswith('django.')}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
