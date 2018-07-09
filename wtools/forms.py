import datetime, imaplib, requests, socket

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.utils import timezone

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, ButtonHolder, Div, Fieldset, HTML, Layout, Submit


class APIRequestMixin(object):
    def apir(self, path, method='GET', data={}):
        api_key = settings.API_KEY
        api_url = settings.API_URL + path
        if method == 'GET':
            r = requests.get(api_url, headers={'Authorization': 'Token %s' % api_key})
        elif method == 'POST':
            r = requests.post(api_url, headers={'Authorization': 'Token %s' % api_key}, data=data)
        elif method == 'PATCH':
            r = requests.patch(api_url, headers={'Authorization': 'Token %s' % api_key}, data=data)
        elif method == 'DELETE':
            r = requests.delete(api_url, headers={'Authorization': 'Token %s' % api_key})
        else:
            raise ValueError('Unknown HTTP method %s' % method)

        if r.status_code in [200, 201]:
            return r.json()
        elif r.status_code == 204:
            return {}
        elif r.status_code == 401:
            raise forms.ValidationError(_('session has expired.'))
        elif r.status_code == 403:
            raise PermissionDenied
        elif r.status_code == 404:
            raise Http404
        else:
            raise forms.ValidationError(str(r.text))


class EmailPasswordChangeForm(APIRequestMixin, forms.Form):
    email = forms.EmailField(label=__('Email'), max_length=254, required=True)
    current_password = forms.CharField(label=__('Password'), max_length=80, required=True, widget=forms.PasswordInput)
    new_password = forms.CharField(label=__('New password'), max_length=80, required=True, widget=forms.PasswordInput)

    api_url = settings.API_URL + 'domain/'

    def __init__(self, *args, **kwargs):
        super(EmailPasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(_('Login'), 'username', 'password', ),
            ButtonHolder(
                Submit('login', _('Login'), css_class='btn btn-primary '),
                )
            )

        self.helper.add_input(Submit('login', 'Login'))

    def get_domains(self):
        domain_dict = cache.get('domain_dict')
        if domain_dict == None:
            domain_dict = {}
            for domain in self.apir('/domain/'):
                domain_dict[domain['name']] = domain
            cache.set('domain_dict', domain_dict)
        return domain_dict

    def get_mailusers(self):
        mailuser_dict = cache.get('mailuser_dict')
        if mailuser_dict == None:
            mailuser_dict = {}
            for mailuser in self.apir('/mailuser/'):
                mailuser_dict[mailuser['local'] + '@' + mailuser['domain']] = mailuser
            cache.set('mailuser_dict', mailuser_dict)
        return mailuser_dict

    def clean_email(self):
        self.domain_dict = self.get_domains()
        self.mailuser_dict = self.get_mailusers()

        data = self.cleaned_data
        email = data['email']
        if not email in self.mailuser_dict:
            raise forms.ValidationError(_('Access denied.'))

        local, domain = email.split('@')
        if not domain in self.domain_dict:
            raise forms.ValidationError(_('Access denied.'))

        # Load details of the domain (mail_system)
        if not self.domain_dict[domain].get('email'):
            self.domain_dict[domain] = self.apir('/domain/%s/' % self.domain_dict[domain]['id'])
            cache.set('domain_dict', self.domain_dict)
        if not self.domain_dict[domain].get('mail_system'):
            raise forms.ValidationError(_('This email account is not assigned to a mail system.'))
        return email

    def clean_current_password(self):
        data = self.cleaned_data
        email = data.get('email')
        if not email:
            raise forms.ValidationError(_('Access denied.'))
        pwd = data['current_password']
        if not pwd:
            raise forms.ValidationError(_('Access denied.'))

        # Probing access credentials on the IMAP server
        local, domain = email.split('@')
        mailserver = self.domain_dict[domain]['mail_system']['servers'][0]
        socket.setdefaulttimeout(5)
        try:
            M = imaplib.IMAP4_SSL(mailserver['name'])
            M.login(email, pwd)
        except imaplib.IMAP4.error:
            raise forms.ValidationError(_('Invalid password.'))
        except (socket.gaierror, NameError):
            raise forms.ValidationError(_('Invalid mail server hostname %s' % mailserver['name']))
        except socket.error:
            raise forms.ValidationError(_('Connection error'))
        return pwd

    def clean(self):
        super().clean()
        data = self.cleaned_data
        if data.get('email') and data['email'] in self.mailuser_dict:
            data['id'] = self.mailuser_dict[data['email']]['id']
        return data

