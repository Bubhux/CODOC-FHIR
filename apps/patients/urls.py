# apps/patients/urls.py
from django.urls import path

from .views import PatientDetail, PatientList

app_name = "patients"

urlpatterns = [
    path("", PatientList.as_view(), name="patient-list"),
    path("<int:pk>/", PatientDetail.as_view(), name="patient-detail"),
]
