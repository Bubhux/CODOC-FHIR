# dwh_fhir/urls.py
"""
dwh_fhir URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.patients.api_views import PatientListCreateAPIView, PatientRetrieveUpdateDestroyAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Web interface
    path("patient/", include("apps.patients.urls")),
    # API endpoints
    path("api/patient/", PatientListCreateAPIView.as_view(), name="api-patient-list"),
    path("api/patient/<int:pk>/", PatientRetrieveUpdateDestroyAPIView.as_view(), name="api-patient-detail"),
    # Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("", RedirectView.as_view(url="/patient/", permanent=False)),
]
