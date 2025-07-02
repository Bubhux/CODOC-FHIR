# apps/patients/urls.py
from django.urls import path
from .views import PatientList, PatientDetail


app_name = "patients"

urlpatterns = [
    path('', PatientList.as_view(), name='patient-list'),
    path('new/', PatientList.as_view(), name='patient-create'),
    path('<int:pk>/', PatientDetail.as_view(), name='patient-detail'),
    path('<int:pk>/edit/', PatientDetail.as_view(), name='patient-update'),
]
