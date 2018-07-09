from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.views import defaults as default_views

from wtools import views


urlpatterns = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^$', views.EmailPasswordChangeView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

