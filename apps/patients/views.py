# apps/patients/views.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast

from django.contrib import messages
from django.core.paginator import Page, Paginator
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Patient
from .serializers import PatientFHIRSerializer


class PatientMixin:
    """Mixin contenant les méthodes communes aux vues Patient."""

    def extract_patient_extensions(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait les données étendues du patient (lieu de naissance, coordonnées, etc.).

        Args:
            patient_data: Données du patient au format dict FHIR

        Returns
        -------
        Dict[str, Any]
            Données du patient enrichies avec les extensions extraites
        """
        data = patient_data.copy()

        # Extraire date de décès
        deceased_datetime = None
        residence_latitude = residence_longitude = None
        birth_city = birth_zip_code = birth_country = None
        birth_latitude = birth_longitude = None

        for ext in data.get("extension", []):
            if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/patient-deathDate":
                deceased_datetime = ext.get("valueDateTime")
            elif ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
                for sub_ext in ext.get("extension", []):
                    if sub_ext["url"] == "latitude":
                        residence_latitude = sub_ext["valueDecimal"]
                    elif sub_ext["url"] == "longitude":
                        residence_longitude = sub_ext["valueDecimal"]
            elif ext.get("url") == "http://hl7.org/fhir/StructureDefinition/patient-birthPlace":
                addr = ext.get("valueAddress", {})
                birth_city = addr.get("city")
                birth_zip_code = addr.get("postalCode")
                birth_country = addr.get("country")
                for sub_ext in ext.get("extension", []):
                    if sub_ext["url"] == "http://hl7.org/fhir/StructureDefinition/geolocation":
                        for geo in sub_ext.get("extension", []):
                            if geo["url"] == "latitude":
                                birth_latitude = geo["valueDecimal"]
                            elif geo["url"] == "longitude":
                                birth_longitude = geo["valueDecimal"]

        # Formatage date
        if deceased_datetime:
            deceased_datetime = deceased_datetime[:16]
        data["deceasedDateTime_formatted"] = deceased_datetime

        # Ajout des données extraites
        data.update(
            {
                "residence_latitude": residence_latitude,
                "residence_longitude": residence_longitude,
                "birth_city": birth_city,
                "birth_zip_code": birth_zip_code,
                "birth_country": birth_country,
                "birth_latitude": birth_latitude,
                "birth_longitude": birth_longitude,
            }
        )

        return data

    def form_to_fhir(self, form_data: Dict[str, Any], patient_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """
        Convertit les données du formulaire en structure FHIR.

        Args:
            form_data: Données issues d'un formulaire HTML ou similaire
            patient_id: Identifiant patient (optionnel)

        Returns
        -------
        Dict[str, Any]
            Données formatées au standard FHIR pour Patient
        """
        fhir_data: Dict[str, Any] = {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [
                {
                    "system": "urn:oid:1.2.250.1.213.1.4.8",
                    "value": form_data.get("ipp") or form_data.get("identifier.0.value"),
                }
            ],
            "name": [
                {
                    "family": form_data.get("last_name") or form_data.get("name.0.family"),
                    "given": [form_data.get("first_name") or form_data.get("name.0.given.0")],
                    "maiden": form_data.get("maiden_name") or form_data.get("name.0.maiden") or None,
                }
            ],
            "gender": form_data.get("sex") or form_data.get("gender"),
            "birthDate": form_data.get("birth_date") or form_data.get("birthDate"),
            "telecom": (
                [{"system": "phone", "value": form_data.get("phone_number") or form_data.get("telecom.0.value")}]
                if form_data.get("phone_number") or form_data.get("telecom.0.value")
                else []
            ),
            "address": (
                [
                    {
                        "line": (
                            [form_data.get("residence_address") or form_data.get("address.0.line.0")]
                            if form_data.get("residence_address") or form_data.get("address.0.line.0")
                            else []
                        ),
                        "city": form_data.get("residence_city") or form_data.get("address.0.city"),
                        "postalCode": form_data.get("residence_zip_code") or form_data.get("address.0.postalCode"),
                        "country": form_data.get("residence_country") or form_data.get("address.0.country"),
                    }
                ]
                if any(
                    [
                        form_data.get("residence_address") or form_data.get("address.0.line.0"),
                        form_data.get("residence_city") or form_data.get("address.0.city"),
                        form_data.get("residence_zip_code") or form_data.get("address.0.postalCode"),
                        form_data.get("residence_country") or form_data.get("address.0.country"),
                    ]
                )
                else []
            ),
            # On garantit que 'extension' est une liste de dicts
            "extension": [],
        }

        # Assertion pour mypy
        extensions = cast(List[Dict[str, Any]], fhir_data["extension"])

        residence_lat = form_data.get("residence_latitude")
        residence_lon = form_data.get("residence_longitude")
        if residence_lat and residence_lon:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {"url": "latitude", "valueDecimal": float(str(residence_lat).replace(",", "."))},
                        {"url": "longitude", "valueDecimal": float(str(residence_lon).replace(",", "."))},
                    ],
                }
            )

        birth_city = form_data.get("birth_city")
        birth_zip = form_data.get("birth_zip_code")
        birth_country = form_data.get("birth_country")
        birth_lat = form_data.get("birth_latitude")
        birth_lon = form_data.get("birth_longitude")

        if any([birth_city, birth_zip, birth_country, birth_lat, birth_lon]):
            birth_place: Dict[str, Any] = {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
                "valueAddress": {"city": birth_city, "postalCode": birth_zip, "country": birth_country},
            }

            if birth_lat and birth_lon:
                birth_place["extension"] = [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                        "extension": [
                            {"url": "latitude", "valueDecimal": float(str(birth_lat).replace(",", "."))},
                            {"url": "longitude", "valueDecimal": float(str(birth_lon).replace(",", "."))},
                        ],
                    }
                ]

            extensions.append(birth_place)

        death_code = form_data.get("death_code")
        death_date = form_data.get("deceasedDateTime")

        if death_code:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-deathCause",
                    "valueCodeableConcept": {
                        "coding": [{"system": "urn:oid:1.2.250.1.213.1.4.5.2", "code": death_code}]
                    },
                }
            )

        if death_date:
            try:
                death_date_iso = datetime.strptime(death_date, "%Y-%m-%dT%H:%M").isoformat()
            except (ValueError, TypeError):
                death_date_iso = death_date

            extensions.append(
                {"url": "http://hl7.org/fhir/StructureDefinition/patient-deathDate", "valueDateTime": death_date_iso}
            )

        fhir_data["meta"] = {"lastUpdated": datetime.now().isoformat()}

        return fhir_data


@extend_schema_view(
    get=extend_schema(
        operation_id="list_patients", summary="Liste des patients", description="Récupère la liste des patients"
    ),
    post=extend_schema(
        operation_id="create_patient", summary="Créer un patient", description="Crée un nouveau patient"
    ),
)
@method_decorator(csrf_exempt, name="dispatch")
class PatientList(APIView, PatientMixin):
    """Gère la liste des patients et la création."""

    serializer_class = PatientFHIRSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def get(self, request: Request, format: Optional[str] = None) -> Union[HttpResponse, Response]:
        """Liste les patients ou affiche le formulaire de création."""
        # Si le paramètre 'new' est présent, afficher le formulaire de création
        if request.GET.get("new") == "true":
            return render(request, "patients/patient_create.html", {})

        # Sinon, afficher la liste des patients
        patients = Patient.objects.all().order_by("id")
        paginator = Paginator(patients, 15)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        serializer = PatientFHIRSerializer(page_obj, many=True)

        if request.accepted_renderer.format == "html" or "text/html" in request.headers.get("Accept", ""):
            return render(request, "patients/patient_list.html", {"patients": serializer.data, "page_obj": page_obj})
        return Response(serializer.data)

    def post(self, request: Request, format: Optional[str] = None) -> Union[HttpResponse, Response]:
        """Crée un nouveau patient."""
        # Gestion du formulaire HTML
        if request.content_type == "application/x-www-form-urlencoded":
            fhir_data = self.form_to_fhir(request.POST)
            serializer = PatientFHIRSerializer(data=fhir_data)

            if serializer.is_valid():
                patient = serializer.save()
                messages.success(request, "Le patient a été créé avec succès!")
                return redirect(f"/Patient/{patient.id}/")

            return render(
                request,
                "patients/patient_create.html",
                {"errors": serializer.errors, "form_data": request.POST},
                content_type="text/html",
            )

        # Gestion API JSON
        serializer = PatientFHIRSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            return Response(
                PatientFHIRSerializer(patient).data,
                status=status.HTTP_201_CREATED,
                headers={"Location": f"/patient/{patient.id}/"},
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        operation_id="retrieve_patient",
        summary="Détail d'un patient",
        description="Récupère les informations d'un patient spécifique",
    ),
    put=extend_schema(
        operation_id="update_patient",
        summary="Mettre à jour un patient",
        description="Met à jour complètement un patient existant",
    ),
    post=extend_schema(
        operation_id="update_patient_via_form",
        summary="Mettre à jour via formulaire",
        description="Met à jour un patient via formulaire HTML",
    ),
    delete=extend_schema(
        operation_id="delete_patient", summary="Supprimer un patient", description="Supprime un patient existant"
    ),
)
@method_decorator(csrf_exempt, name="dispatch")
class PatientDetail(APIView, PatientMixin):
    """Gère les opérations sur un patient spécifique."""

    serializer_class = PatientFHIRSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def get(self, request: Request, pk: int, format: Optional[str] = None) -> Union[HttpResponse, Response]:
        """Affiche un patient (détail ou formulaire de modification)."""
        patient = get_object_or_404(Patient, pk=pk)
        serializer = PatientFHIRSerializer(patient)
        data = self.extract_patient_extensions(serializer.data)

        if request.accepted_renderer.format == "html" or "text/html" in request.headers.get("Accept", ""):
            # Si le paramètre 'edit' est présent, afficher le formulaire de modification
            if request.GET.get("edit") == "true":
                return render(request, "patients/patient_update.html", {"patient": data})
            # Sinon afficher la vue détail
            return render(request, "patients/patient_detail.html", {"patient": data})

        return Response(data)

    def post(self, request: Request, pk: int, format: Optional[str] = None) -> Union[HttpResponse, Response]:
        """Gère les actions via formulaire HTML (modification ou suppression)."""
        if request.content_type == "application/x-www-form-urlencoded":
            # Si c'est une demande de suppression
            if request.POST.get("_method") == "DELETE":
                return self.delete(request, pk, format)
            # Sinon c'est une mise à jour
            return self.put(request, pk, format)
        return Response({"detail": "Méthode POST non autorisée"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def put(self, request: Request, pk: int, format: Optional[str] = None) -> Union[HttpResponse, Response]:
        """Met à jour un patient."""
        patient = get_object_or_404(Patient, pk=pk)

        if request.content_type == "application/x-www-form-urlencoded":
            # Gestion formulaire HTML
            fhir_data = self.form_to_fhir(request.POST, patient.id)
            serializer = PatientFHIRSerializer(patient, data=fhir_data)

            if serializer.is_valid():
                try:
                    serializer.save()
                    messages.success(request, "Patient mis à jour avec succès")
                    return redirect(f"/Patient/{pk}/")
                except IntegrityError as e:
                    messages.error(request, f"Erreur de base de données: {str(e)}")
                    return render(
                        request,
                        "patients/patient_update.html",
                        {"patient": patient, "errors": {"IPP": "Erreur de contrainte d'intégrité"}},
                        status=400,
                    )

            # Si erreur de validation, réaffiche le formulaire
            return render(
                request, "patients/patient_update.html", {"patient": patient, "errors": serializer.errors}, status=400
            )

        # Gestion API
        serializer = PatientFHIRSerializer(patient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Request, pk: int, format: Optional[str] = None) -> Response:
        """Supprime un patient."""
        patient = get_object_or_404(Patient, pk=pk)
        patient.delete()

        if request.accepted_renderer.format == "html" or "text/html" in request.headers.get("Accept", ""):
            messages.success(request, "Patient supprimé avec succès")
            return redirect("/Patient/")

        return Response(status=status.HTTP_204_NO_CONTENT)
