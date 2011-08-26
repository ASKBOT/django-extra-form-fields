import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
import sys

import django_extra_form_fields

setup(
    name = "django_extra_form_fields",
    version = django_extra_form_fields.get_version(),
    description = 'Additional form fields for Django applications',
    packages = find_packages(),
    author = 'Evgeny.Fadeev',
    author_email = 'evgeny.fadeev@gmail.com',
    license = 'GPLv3',
    keywords = 'django, module',
    url = 'http://askbot.org',
    include_package_data = True,
    long_description = """Additional form fields to use in Django applications:

* NextUrlField - add to forms that need to store url of next page
* get_next_url - utility function to extract next url from the request object
* UserNameField - field to enter user name - allows unique username site-wide
* UserEmailField - allows unique email address site-wide if ``EMAIL_UNIQUE`` setting is ``True``
"""
)
