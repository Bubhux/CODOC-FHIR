# apps/patients/views.py
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from .models import Patient
from .serializers import PatientFHIRSerializer


class PatientList(APIView):
    """
    Liste tous les patients ou crée un nouveau patient.
    """

    def get(self, request, format=None):
        patients = Patient.objects.all()
        serializer = PatientFHIRSerializer(patients, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = PatientFHIRSerializer(data=request.data)

        # Gestion de l'en-tête If-None-Exist
        if_none_exist = request.headers.get('If-None-Exist')
        if if_none_exist:
            # Ici on pourrait vérifier si un patient similaire existe déjà
            # Pour simplifier, on vérifie juste l'IPP
            ipp = next((id['value'] for id in request.data.get('identifier', [])
                       if id.get('system') == 'urn:oid:1.2.250.1.213.1.4.8'), None)
            if ipp and Patient.objects.filter(ipp=ipp).exists():
                return Response(status=status.HTTP_412_PRECONDITION_FAILED)

        if serializer.is_valid():
            serializer.save()

            # Gestion de l'en-tête Prefer
            prefer = request.headers.get('Prefer', 'return=minimal')
            if prefer == 'return=representation':
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(status=status.HTTP_201_CREATED, headers={
                    'Location': f'/patient/{serializer.data["id"]}/'
                })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientDetail(APIView):
    """
    Récupère, met à jour ou supprime un patient.
    """

    def get_object(self, pk):
        try:
            return Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        patient = self.get_object(pk)
        serializer = PatientFHIRSerializer(patient)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        patient = self.get_object(pk)
        serializer = PatientFHIRSerializer(patient, data=request.data)
        if serializer.is_valid():
            serializer.save()

            # Gestion de l'en-tête Prefer
            prefer = request.headers.get('Prefer', 'return=minimal')
            if prefer == 'return=representation':
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        patient = self.get_object(pk)
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
