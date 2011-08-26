from django import forms
import re
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
#todo - use unified settings abject
from django.conf import settings as django_settings
from askbot.conf import settings as askbot_settings
from django.http import str_to_unicode
from django.contrib.auth.models import User
from askbot import const
import logging
import urllib

class StrippedNonEmptyCharField(forms.CharField):
    """``CharField`` with a requirement of
    being a non-empty string"""
    def clean(self,value):
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
            django_settings.LOGIN_REDIRECT_URL
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
    RESERVED_USER_NAMES = (
        u'fuck', u'shit', u'ass', u'sex', u'add',
        u'edit', u'save', u'delete', u'manage',
        u'update', 'remove', 'new'
    )
    def __init__(self, **kwargs):
        """optional parameters:
        * ``skip_clean`` - boolean, if true - do not clean user name, just return
        * ``user_instance`` - instance of ``class::auth.models.User`` - if given,
          username will work if it is the same as that of user_instance
        """
        self.skip_clean = kwargs.pop('skip_clean', False)
        self.user_instance = kwargs.pop('user_instance', None)
        kwargs.setdefault('label', _('choose a user name'))
        kwargs.setdefault('max_length', 30)

        #widget parameters
        widget_attrs = kwargs.pop('widget_attrs', {})
        default_widget = forms.TextInput(attrs = widget_attrs)
        kwargs.setdefault('widget', default_widget)

        #error messages
        self.error_messages={
            'required':_('user name is required'),
            'taken':_('sorry, this name is taken, please choose another'),
            'forbidden':_('sorry, this name is not allowed, please choose another'),
            'missing':_('sorry, there is no user with this name'),
            'multiple-taken':_('sorry, we have a serious error - user name is taken by several users'),
            'invalid':_('user name can only consist of letters, empty space and underscore'),
        }
        extra_messages = kwargs.pop('error_messages', {})
        self.error_messages.update(extra_messages)

        super(UserNameField,self).__init__(**kwargs)

    def clean(self, username):
        """ validate username """
        if self.skip_clean == True:
            logging.debug('username accepted with no validation')
            return username
        if self.user_instance is None:
            pass
        elif isinstance(self.user_instance, User):
            if username == self.user_instance.username:
                logging.debug('username valid')
                return username
        else:
            raise TypeError('user instance must be of type User')

        try:
            username = super(UserNameField, self).clean(username)
        except forms.ValidationError:
            raise forms.ValidationError(self.error_messages['required'])

        username_regex = re.compile(const.USERNAME_REGEX_STRING, re.UNICODE)
        if self.required and not username_regex.search(username):
            raise forms.ValidationError(self.error_messages['invalid'])
        if username in self.RESERVED_USER_NAMES:
            raise forms.ValidationError(self.error_messages['forbidden'])
        try:
            User.objects.get(username = username)
            raise forms.ValidationError(self.error_messages['taken'])
        except User.DoesNotExist:
            return username
        except User.MultipleObjectsReturned:
            logging.debug('error - user with this name already exists')
            raise forms.ValidationError(self.error_messages['multiple-taken'])

class UserEmailField(forms.EmailField):
    def __init__(self, **kwargs):
        """optional keyword arguments:
        * widget - form widget
        * widget_attrs - attributes for the field widget
        """
        kwargs.setdefault('label', mark_safe(_('your email address')))

        error_messages = {
            'required':_('email address is required'),
            'invalid':_('please enter a valid email address'),
            'taken':_('this email is already used by someone else, please choose another'),
        }
        error_messages.update(kwargs.get('error_messages', {}))
        kwargs['error_messages'] = error_messages

        widget_attrs = kwargs.pop('widget_attrs', {})
        kwargs.setdefault('widget', forms.TextInput(attrs = widget_attrs))

        super(UserEmailField,self).__init__(**kwargs)

    def clean(self, email):
        """ validate if email exist in database
        from legacy register
        return: raise error if it exist """
        email = super(UserEmailField, self).clean(email.strip())
        if askbot_settings.EMAIL_UNIQUE == True:
            try:
                user = User.objects.get(email = email)
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
