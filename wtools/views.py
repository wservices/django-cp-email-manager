import requests

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.views.generic import FormView, TemplateView, DeleteView, UpdateView

from ratelimit.mixins import RatelimitMixin

from wtools import forms


class EmailPasswordChangeView(RatelimitMixin, FormView):
    form_class = forms.EmailPasswordChangeForm
    template_name = 'wtools/email_password_change.html'
    success_url = '/'
    ratelimit_key = 'ip'
    ratelimit_rate = '5/h'
    ratelimit_block = True
    ratelimit_method = 'POST'

    def form_valid(self, form):
        data = form.cleaned_data
        pwd = data['new_password']
        api_key = settings.API_KEY
        api_url = settings.API_URL + 'mailuser/%s/' % data['id']
        r = requests.patch(api_url, headers={'Authorization': 'Token %s' % api_key}, data={'password': pwd})
        if r.status_code == 200:
            messages.add_message(self.request, messages.INFO, _('Password has been changed.'))
        else:
            messages.add_message(self.request, messages.ERROR, r.text)
        return super().form_valid(form)

