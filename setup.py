import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

import django_extra_form_fields

setup(
    name = "django_extra_form_fields",
    version = django_extra_form_fields.__version__,
    description = 'Additional form fields for Django applications',
    packages = find_packages(),
    author = 'Evgeny.Fadeev',
    author_email = 'evgeny.fadeev@gmail.com',
    license = 'BSD',
    keywords = 'django, module',
    url = 'http://askbot.org',
    include_package_data = True,
    install_requires = [
        'multi_registry',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    long_description = """Additional form fields to use in Django applications:

* NextUrlField - add to forms that need to store url of next page
* get_next_url - utility function to extract next url from the request object
* UserNameField - field to enter user name - allows unique username site-wide
* UserEmailField - allows unique email address site-wide if ``EMAIL_UNIQUE`` setting is ``True``
"""
)
