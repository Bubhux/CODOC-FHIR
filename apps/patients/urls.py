# apps/patients/urls.py
from django.urls import path

from .web_views import PatientHTMLView

web_view = PatientHTMLView()
app_name = "patients"

# Supprimer les URLs API de ce fichier, elles sont maintenant dans dwh_fhir/urls.py
urlpatterns = [
    # Web Interface seulement
    path("", web_view.list_patients, name="patient-list"),
    path("new/", web_view.create_patient_form, name="patient-create-form"),
    path("create/", web_view.handle_create_patient, name="patient-create"),
    path("<int:pk>/", web_view.patient_detail, name="patient-detail"),
    path("<int:pk>/edit/", web_view.edit_patient_form, name="patient-edit-form"),
    path("<int:pk>/update/", web_view.handle_edit_patient, name="patient-update"),
    path("<int:pk>/delete/", web_view.handle_delete_patient, name="patient-delete"),
]
