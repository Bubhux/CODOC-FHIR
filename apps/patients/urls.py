# apps/patients/urls.py
from django.urls import path
from .views import PatientList, PatientDetail


app_name = "patients"

urlpatterns = [
    path('Patient/', PatientList.as_view(), name='patient-list'),
    path('Patient/<int:pk>/', PatientDetail.as_view(), name='patient-detail'),
]