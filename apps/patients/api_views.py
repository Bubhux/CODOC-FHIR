# apps/patients/api_views.py
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Patient
from .serializers import PatientFHIRSerializer


class PatientListCreateAPIView(APIView):
    """Endpoint pour la création et la liste des patients (sans ID dans l'URL)."""

    serializer_class = PatientFHIRSerializer

    @extend_schema(
        operation_id="patient_api_patient_create", description="Créer un nouveau patient selon le standard FHIR"
    )
    def post(self, request: Request) -> Response:
        """Créer un nouveau patient selon le standard FHIR."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers={"Location": f"/patient/{serializer.instance.id}/"},
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(operation_id="patient_api_patient_list", description="Lister tous les patients")
    def get(self, request: Request) -> Response:
        """Lister tous les patients (implémentez selon vos besoins)."""
        patients = Patient.objects.all()
        serializer = self.serializer_class(patients, many=True)
        return Response(serializer.data)


class PatientRetrieveUpdateDestroyAPIView(APIView):
    """Endpoint pour la récupération, mise à jour et suppression d'un patient spécifique (avec ID dans l'URL)."""

    serializer_class = PatientFHIRSerializer

    @extend_schema(operation_id="patient_api_patient_retrieve", description="Récupérer un patient spécifique")
    def get(self, request: Request, pk: int) -> Response:
        """Récupérer un patient spécifique."""
        patient = get_object_or_404(Patient, pk=pk)
        serializer = self.serializer_class(patient)
        return Response(serializer.data)

    @extend_schema(operation_id="patient_api_patient_update", description="Mettre à jour complètement un patient")
    def put(self, request: Request, pk: int) -> Response:
        """Mettre à jour complètement un patient."""
        patient = get_object_or_404(Patient, pk=pk)
        serializer = self.serializer_class(patient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(operation_id="patient_api_patient_delete", description="Supprimer un patient")
    def delete(self, request: Request, pk: int) -> Response:
        """Supprimer un patient."""
        patient = get_object_or_404(Patient, pk=pk)
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
