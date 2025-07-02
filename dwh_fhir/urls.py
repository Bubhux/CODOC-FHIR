# dwh_fhir/urls.py
"""
dwh_fhir URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('Patient/', include('apps.patients.urls')),  # Préfixe centralisé
    path('', RedirectView.as_view(url='/Patient/', permanent=False)),  # Redirige vers /Patient/
]
