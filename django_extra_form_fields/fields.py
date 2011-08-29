"""module ``django_extra_form_fields`` 
provides several additional form fields:
* StrippedNonEmptyCharField
* NextUrlField (and an accompanying method ``get_next_url``)
* UserNameField
* UserEmailField
"""
import logging
import re
import urllib
from django import forms
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
#todo - use unified settings abject
from django_extra_form_fields.conf import settings
from django.http import str_to_unicode
from django.contrib.auth.models import User

class StrippedNonEmptyCharField(forms.CharField):
    """``CharField`` with a requirement of
    being a non-empty string"""
    def clean(self, value):
        """Clean function strips the value
        of empty characters"""
        value = value.strip()
        if self.required and value == '':
            raise forms.ValidationError(_('this field is required'))
        return value

class NextUrlField(forms.CharField):
    """Field allowing to add parameter "next_url"
    so that user could be redirected to specific url
    after the form is submitted.

    the next url defaults to the value of
    parameter ``default_next_url``, if given 
    at the initialization, or by the django setting
    ``LOGIN_REDIRECT_URL``.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 255)
        kwargs.setdefault('widget', forms.HiddenInput())
        kwargs.setdefault('required', False)
        self.default_next_url = kwargs.pop(
            'default_next_url',
            settings.LOGIN_REDIRECT_URL
        )
        super(NextUrlField, self).__init__(**kwargs)

    def clean(self, value):
        if value is None:
            return self.default_next_url
        value = str_to_unicode(urllib.unquote(value), 'utf-8').strip()
        assert(value.startswith('/'))
        return value


def get_next_url(request, field_name = 'next'):
    """extracts value of field from request - 
    either POST or GET dictionaries and cleans the value
    via the ``NextUrlField`` form field"""
    field = NextUrlField()
    return field.clean(request.REQUEST.get(field_name))


class UserNameField(StrippedNonEmptyCharField):
    """Checks existence of user name in the database.
    If name already exist, value of the field will not
    validate.

    Allows to validate user name against
    a custom regex, which defaults to the django's 
    internal username regex given by setting -
    ``USERNAME_REGEX_STRING``

    Allows to specify list of names that cannot
    be used via setting ``RESERVED_USER_NAMES``
    """
    def __init__(self, **kwargs):
        """optional parameters:
        * ``skip_clean`` - boolean, if true - do not clean user name, just return
        * ``widget_attrs`` - attributes to pass onto the widget
        """
        self.skip_clean = kwargs.pop('skip_clean', False)
        kwargs.setdefault('label', _('choose a user name'))
        kwargs.setdefault('max_length', 30)

        #widget parameters
        widget_attrs = kwargs.pop('widget_attrs', {})
        default_widget = forms.TextInput(attrs = widget_attrs)
        kwargs.setdefault('widget', default_widget)

        #error messages
        self.error_messages = {
            'required':_('user name is required'),
            'taken':_('sorry, this name is taken, please choose another'),
            'forbidden':_(
                'sorry, this name is not allowed, '
                'please choose another'
            ),
            'missing':_('sorry, there is no user with this name'),
            'multiple-taken':_(
                'sorry, we have a serious error '
                '- user name is taken by several users'
            ),
            'invalid':_(
                'user name can only consist of letters, numbers, '
                'and @/./+/-/_ characters.'
            ),
        }
        extra_messages = kwargs.pop('error_messages', {})
        self.error_messages.update(extra_messages)

        super(UserNameField, self).__init__(**kwargs)

    def clean(self, username):
        """ validate username """
        if self.skip_clean == True:
            logging.debug('username accepted with no validation')
            return username

        try:
            username = super(UserNameField, self).clean(username)
        except forms.ValidationError:
            raise forms.ValidationError(self.error_messages['required'])

        username_regex = re.compile(settings.USERNAME_REGEX_STRING, re.UNICODE)
        if self.required and not username_regex.search(username):
            raise forms.ValidationError(self.error_messages['invalid'])
        if hasattr(settings, 'RESERVED_USER_NAMES'):
            if username in settings.RESERVED_USER_NAMES:
                raise forms.ValidationError(self.error_messages['forbidden'])

        #Check whether user name is available.
        #there is a race condition
        #here, where it is possibility for an uncaught database
        #error, but it will be very rare, so we ignore it
        try:
            if username == self.initial:
                #skip uniqueness testing here because user is
                #not changing his name
                return username
            else:
                User.objects.get(username = username)
                raise forms.ValidationError(self.error_messages['taken'])
        except User.DoesNotExist:
            return username
        except User.MultipleObjectsReturned:
            logging.debug('error - user with this name already exists')
            raise forms.ValidationError(self.error_messages['multiple-taken'])

class UserEmailField(forms.EmailField):
    """Same as :class:`django.forms.EmailField`, but
    allows checking for the email unqueness - if setting
    ``EMAIL_UNIQUE`` == True
    """
    def __init__(self, **kwargs):
        """optional keyword arguments:
        * widget - form widget
        * widget_attrs - attributes for the field widget
        """
        kwargs.setdefault('label', mark_safe(_('your email address')))

        error_messages = {
            'required':_('email address is required'),
            'invalid':_('please enter a valid email address'),
            'taken':_(
                'this email is already used by someone else, '
                'please choose another'
            ),
        }
        error_messages.update(kwargs.get('error_messages', {}))
        kwargs['error_messages'] = error_messages

        widget_attrs = kwargs.pop('widget_attrs', {})
        kwargs.setdefault('widget', forms.TextInput(attrs = widget_attrs))

        super(UserEmailField, self).__init__(**kwargs)

    def clean(self, email):
        """ validate if email exist in database
        from legacy register
        return: raise error if it exist """
        email = super(UserEmailField, self).clean(email.strip())
        if settings.EMAIL_UNIQUE == True:
            try:
                User.objects.get(email = email)
                logging.debug('email taken')
                raise forms.ValidationError(self.error_messages['taken'])
            except User.DoesNotExist:
                logging.debug('email valid')
                return email
            except User.MultipleObjectsReturned:
                logging.debug('email taken many times over')
                raise forms.ValidationError(self.error_messages['taken'])
        else:
            return email 
