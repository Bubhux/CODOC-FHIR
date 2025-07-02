# apps/patients/views.py
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Patient
from .serializers import PatientFHIRSerializer


class PatientList(APIView):
    """Liste tous les patients ou crée un nouveau patient conformément à FHIR."""

    def get(self, request, format=None):
        patients = Patient.objects.all()
        serializer = PatientFHIRSerializer(patients, many=True)

        # Si HTML demandé
        if request.accepted_renderer.format == 'html' or 'text/html' in request.headers.get('Accept', ''):
            return render(
                request,
                'patients/patient_list.html',
                {'patients': serializer.data},
                content_type='text/html'
            )

        # Sinon retourner JSON
        return Response(serializer.data)

    def post(self, request, format=None):
        # Validation FHIR de base
        if not request.data.get('resourceType') == 'Patient':
            return Response(
                {"error": "resourceType must be 'Patient'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Gestion If-None-Exist
        if_none_exist = request.headers.get('If-None-Exist')
        if if_none_exist:
            ipp = next(
                (id['value'] for id in request.data.get('identifier', [])
                if id.get('system') == 'urn:oid:1.2.250.1.213.1.4.8'),
                None
            )
            if ipp and Patient.objects.filter(ipp=ipp).exists():
                return Response(
                    {"error": "Patient already exists with this IPP"},
                    status=status.HTTP_412_PRECONDITION_FAILED
                )

        serializer=PatientFHIRSerializer(data=request.data)
        if serializer.is_valid():
            patient=serializer.save()

            # Réponse selon l'en-tête Prefer
            prefer=request.headers.get('Prefer', 'return=minimal')
            if prefer == 'return=representation':
                response_data=PatientFHIRSerializer(patient).data
                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED,
                    headers={'Location': f'/patient/{patient.id}/'}
                )
            else:
                return Response(
                    status=status.HTTP_201_CREATED,
                    headers={'Location': f'/patient/{patient.id}/'}
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientDetail(APIView):
    """Opérations CRUD sur un patient spécifique conformément à FHIR."""

    def get_object(self, pk):
        return get_object_or_404(Patient, pk=pk)

    def get(self, request, pk, format=None):
        patient = self.get_object(pk)
        serializer = PatientFHIRSerializer(patient)

        # Si le client accepte HTML, renvoyer le template
        if request.accepted_renderer.format == 'html' or 'text/html' in request.headers.get('Accept', ''):
            return render(request, 'patients/patient_detail.html', {'patient': serializer.data})

        # Sinon, renvoyer le JSON habituel
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        patient=self.get_object(pk)

        # Validation FHIR de base
        if not request.data.get('resourceType') == 'Patient':
            return Response(
                {"error": "resourceType must be 'Patient'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if str(request.data.get('id')) != str(pk):
            return Response(
                {"error": "Patient ID in URL and body must match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer=PatientFHIRSerializer(patient, data=request.data)
        if serializer.is_valid():
            updated_patient=serializer.save()

            # Réponse selon l'en-tête Prefer
            prefer=request.headers.get('Prefer', 'return=minimal')
            if prefer == 'return=representation':
                response_data=PatientFHIRSerializer(updated_patient).data
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        patient=self.get_object(pk)
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
