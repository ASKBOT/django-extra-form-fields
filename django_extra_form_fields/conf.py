"""settings module for 
django_extra_form_fields

the following settings can be added to
django settings or the extra settings module:

* RESERVED_USER_NAMES - a tuple or a list of forbidden names
* USERNAME_REGEX_STRING - regex for acceptable user name
* EMAIL_UNIQUE - boolean - require unique email address sitewide
"""
from django.conf import settings as django_settings
from multi_registry import MultiRegistry

settings = MultiRegistry(
    django_settings,
    'django_extra_form_fields.default_settings'
)
extra_settings = getattr(django_settings, 'EXTRA_SETTINGS_MODULE', None)
if extra_settings:
    settings.insert(1, extra_settings)

