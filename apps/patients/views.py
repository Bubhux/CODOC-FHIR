# apps/patients/views.py
from django.shortcuts import get_object_or_404, render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from datetime import datetime

from .models import Patient
from .serializers import PatientFHIRSerializer


class PatientMixin:
    """Mixin contenant les méthodes communes aux vues Patient"""

    def extract_patient_extensions(self, patient_data):
        """Extrait les données étendues du patient (lieu de naissance, coordonnées, etc.)"""
        data = patient_data.copy()

        # Extraire date de décès
        deceased_datetime = None
        residence_latitude = residence_longitude = None
        birth_city = birth_zip_code = birth_country = None
        birth_latitude = birth_longitude = None

        for ext in data.get('extension', []):
            if ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/patient-deathDate':
                deceased_datetime = ext.get('valueDateTime')
            elif ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/geolocation':
                for sub_ext in ext.get('extension', []):
                    if sub_ext['url'] == 'latitude':
                        residence_latitude = sub_ext['valueDecimal']
                    elif sub_ext['url'] == 'longitude':
                        residence_longitude = sub_ext['valueDecimal']
            elif ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/patient-birthPlace':
                addr = ext.get('valueAddress', {})
                birth_city = addr.get('city')
                birth_zip_code = addr.get('postalCode')
                birth_country = addr.get('country')
                for sub_ext in ext.get('extension', []):
                    if sub_ext['url'] == 'http://hl7.org/fhir/StructureDefinition/geolocation':
                        for geo in sub_ext.get('extension', []):
                            if geo['url'] == 'latitude':
                                birth_latitude = geo['valueDecimal']
                            elif geo['url'] == 'longitude':
                                birth_longitude = geo['valueDecimal']

        # Formatage date
        if deceased_datetime:
            deceased_datetime = deceased_datetime[:16]
        data['deceasedDateTime_formatted'] = deceased_datetime

        # Ajout des données extraites
        data.update({
            'residence_latitude': residence_latitude,
            'residence_longitude': residence_longitude,
            'birth_city': birth_city,
            'birth_zip_code': birth_zip_code,
            'birth_country': birth_country,
            'birth_latitude': birth_latitude,
            'birth_longitude': birth_longitude,
        })

        return data

    def form_to_fhir(self, form_data, patient_id=None):
        """Convertit les données du formulaire en structure FHIR"""

        fhir_data = {
            'resourceType': 'Patient',
            'id': patient_id,
            'identifier': [{
                'system': 'urn:oid:1.2.250.1.213.1.4.8',
                'value': form_data.get('ipp') or form_data.get('identifier.0.value')
            }],
            'name': [{
                'family': form_data.get('last_name') or form_data.get('name.0.family'),
                'given': [form_data.get('first_name') or form_data.get('name.0.given.0')],
                'maiden': form_data.get('maiden_name') or form_data.get('name.0.maiden') or None
            }],
            'gender': form_data.get('sex') or form_data.get('gender'),
            'birthDate': form_data.get('birth_date') or form_data.get('birthDate'),
            'telecom': [{
                'system': 'phone',
                'value': form_data.get('phone_number') or form_data.get('telecom.0.value')
            }] if form_data.get('phone_number') or form_data.get('telecom.0.value') else [],
            'address': [{
                'line': [form_data.get('residence_address') or form_data.get('address.0.line.0')] if form_data.get('residence_address') or form_data.get('address.0.line.0') else [],
                'city': form_data.get('residence_city') or form_data.get('address.0.city'),
                'postalCode': form_data.get('residence_zip_code') or form_data.get('address.0.postalCode'),
                'country': form_data.get('residence_country') or form_data.get('address.0.country')
            }] if any([
                form_data.get('residence_address') or form_data.get('address.0.line.0'),
                form_data.get('residence_city') or form_data.get('address.0.city'),
                form_data.get('residence_zip_code') or form_data.get('address.0.postalCode'),
                form_data.get('residence_country') or form_data.get('address.0.country')
            ]) else [],
            'extension': []
        }

        # Coordonnées géographiques de résidence
        residence_lat = form_data.get('residence_latitude')
        residence_lon = form_data.get('residence_longitude')
        if residence_lat and residence_lon:
            fhir_data['extension'].append({
                'url': 'http://hl7.org/fhir/StructureDefinition/geolocation',
                'extension': [
                    {
                        'url': 'latitude',
                        'valueDecimal': float(residence_lat.replace(',', '.'))
                    },
                    {
                        'url': 'longitude',
                        'valueDecimal': float(residence_lon.replace(',', '.'))
                    }
                ]
            })

        # Lieu de naissance
        birth_city = form_data.get('birth_city')
        birth_zip = form_data.get('birth_zip_code')
        birth_country = form_data.get('birth_country')
        birth_lat = form_data.get('birth_latitude')
        birth_lon = form_data.get('birth_longitude')

        if any([birth_city, birth_zip, birth_country, birth_lat, birth_lon]):
            birth_place = {
                'url': 'http://hl7.org/fhir/StructureDefinition/patient-birthPlace',
                'valueAddress': {
                    'city': birth_city,
                    'postalCode': birth_zip,
                    'country': birth_country
                }
            }

            if birth_lat and birth_lon:
                birth_place['extension'] = [{
                    'url': 'http://hl7.org/fhir/StructureDefinition/geolocation',
                    'extension': [
                        {
                            'url': 'latitude',
                            'valueDecimal': float(birth_lat.replace(',', '.'))
                        },
                        {
                            'url': 'longitude',
                            'valueDecimal': float(birth_lon.replace(',', '.'))
                        }
                    ]
                }]

            fhir_data['extension'].append(birth_place)

        # Décès
        death_code = form_data.get('death_code')
        death_date = form_data.get('death_date')

        if death_code:
            fhir_data['extension'].append({
                'url': 'http://hl7.org/fhir/StructureDefinition/patient-deathCause',
                'valueCodeableConcept': {
                    'coding': [{
                        'system': 'urn:oid:1.2.250.1.213.1.4.5.2',
                        'code': death_code
                    }]
                }
            })

        if death_date:
            fhir_data['extension'].append({
                'url': 'http://hl7.org/fhir/StructureDefinition/patient-deathDate',
                'valueDateTime': death_date
            })

        # Date de mise à jour
        fhir_data['meta'] = {
            'lastUpdated': datetime.now().isoformat()
        }

        return fhir_data


class PatientList(APIView, PatientMixin):
    """Liste tous les patients ou crée un nouveau patient conformément à FHIR."""

    parser_classes = [FormParser, MultiPartParser, JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, format=None):
        patients = Patient.objects.all()
        serializer = PatientFHIRSerializer(patients, many=True)

        if ('new' in request.path or
            request.accepted_renderer.format == 'html' or
                'text/html' in request.headers.get('Accept', '')):

            if 'new' in request.path:
                return render(
                    request,
                    'patients/patient_create.html',
                    {},
                    content_type='text/html'
                )

            return render(
                request,
                'patients/patient_list.html',
                {'patients': serializer.data},
                content_type='text/html'
            )

        return Response(serializer.data)

    def post(self, request, format=None):
        # Si formulaire HTML
        if request.content_type == 'application/x-www-form-urlencoded':
            fhir_data = self.form_to_fhir(request.POST)
            serializer = PatientFHIRSerializer(data=fhir_data)

            if serializer.is_valid():
                patient = serializer.save()
                messages.success(request, 'Le patient a été créé avec succès!')
                return redirect(f'/Patient/{patient.id}/')

            return render(
                request,
                'patients/patient_create.html',
                {
                    'errors': serializer.errors,
                    'form_data': request.POST
                },
                content_type='text/html'
            )

        # Reste du code pour la gestion FHIR...
        if not request.data.get('resourceType') == 'Patient':
            return Response(
                {"error": "resourceType must be 'Patient'"},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        serializer = PatientFHIRSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()

            prefer = request.headers.get('Prefer', 'return=minimal')
            if prefer == 'return=representation':
                response_data = PatientFHIRSerializer(patient).data
                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED,
                    headers={'Location': f'/Patient/{patient.id}/'}
                )
            else:
                return Response(
                    status=status.HTTP_201_CREATED,
                    headers={'Location': f'/Patient/{patient.id}/'}
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientDetail(APIView, PatientMixin):
    """Opérations CRUD sur un patient spécifique conformément à FHIR."""

    parser_classes = [FormParser, MultiPartParser, JSONParser]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self, pk):
        return get_object_or_404(Patient, pk=pk)

    def get(self, request, pk, format=None):
        patient = self.get_object(pk)
        serializer = PatientFHIRSerializer(patient)
        data = self.extract_patient_extensions(serializer.data)

        if request.accepted_renderer.format == 'html' or 'text/html' in request.headers.get('Accept', ''):
            template = 'patient_update.html' if 'edit' in request.path else 'patient_detail.html'
            return render(request, f'patients/{template}', {'patient': data})

        return Response(data)

    def put(self, request, pk, format=None):
        patient = self.get_object(pk)

        if request.content_type == 'application/x-www-form-urlencoded':
            fhir_data = self.form_to_fhir(request.POST, patient.id)
        else:
            fhir_data = request.data

        serializer = PatientFHIRSerializer(patient, data=fhir_data)
        if serializer.is_valid():
            updated_patient = serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, 'Patient mis à jour avec succès')
                return redirect('patient-detail', pk=pk)

            return Response(PatientFHIRSerializer(updated_patient).data)

        if request.accepted_renderer.format == 'html':
            messages.error(request, 'Erreur de validation')
            context = {
                'patient': self.extract_patient_extensions(PatientFHIRSerializer(patient).data),
                'errors': serializer.errors,
                'form_data': request.POST
            }
            return render(request, 'patients/patient_update.html', context, status=400)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, pk, format=None):
        """Gère la mise à jour via formulaire HTML"""
        patient = self.get_object(pk)

        if request.method == 'GET':
            serializer = PatientFHIRSerializer(patient)
            data = self.extract_patient_extensions(serializer.data)
            return render(request, 'patients/patient_update.html', {'patient': data})

        elif request.method == 'POST':
            fhir_data = self.form_to_fhir(request.POST, patient.id)
            serializer = PatientFHIRSerializer(patient, data=fhir_data)

            if serializer.is_valid():
                serializer.save()
                messages.success(request, 'Patient mis à jour avec succès')
                return redirect('patients:patient-detail', pk=pk)
            else:
                messages.error(request, 'Erreur de validation')
                serializer = PatientFHIRSerializer(patient)
                data = self.extract_patient_extensions(serializer.data)
                return render(request, 'patients/patient_update.html', {
                    'patient': data,
                    'errors': serializer.errors,
                    'form_data': request.POST
                }, status=400)

        return HttpResponseNotAllowed(['GET', 'POST'])

    def delete(self, request, pk, format=None):
        patient = self.get_object(pk)
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
