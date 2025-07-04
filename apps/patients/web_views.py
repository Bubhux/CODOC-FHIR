# apps/patients/web_views.py
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .mixins import PatientMixin
from .models import Patient
from .serializers import PatientFHIRSerializer


class PatientHTMLView(PatientMixin):
    """Endpoints API strictement conformes aux consignes FHIR pour la gestion des patients.

    Le sérialiseur utilisé pour les opérations CRUD.
    """

    def list_patients(self, request: HttpRequest) -> HttpResponse:
        """Liste paginée des patients.

        Args:
            request: La requête HTTP contenant les paramètres de pagination.

        Returns
        -------
            HttpResponse: Réponse HTTP avec la liste paginée des patients.

            - 200 OK avec la liste des patients
        """
        patients = Patient.objects.all().order_by("id")
        paginator = Paginator(patients, 15)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        serializer = PatientFHIRSerializer(page_obj, many=True)
        return render(request, "patients/patient_list.html", {"patients": serializer.data, "page_obj": page_obj})

    def create_patient_form(self, request: HttpRequest) -> HttpResponse:
        """Affiche le formulaire de création d'un patient.

        Args:
            request: La requête HTTP.

        Returns
        -------
            HttpResponse: Réponse HTTP avec le formulaire de création.

            - 200 OK avec le formulaire vide
        """
        return render(request, "patients/patient_create.html", {})

    def handle_create_patient(self, request: HttpRequest) -> HttpResponse:
        """Traite la création d'un patient via formulaire.

        Args:
            request: La requête HTTP contenant les données du formulaire.

        Returns
        -------
            HttpResponse: Réponse HTTP avec le résultat de l'opération.

            - 302 Redirect vers la page du patient si succès
            - 400 Bad Request avec les erreurs si échec
        """
        fhir_data = self.form_to_fhir(request.POST)
        serializer = PatientFHIRSerializer(data=fhir_data)

        if serializer.is_valid():
            patient = serializer.save()
            messages.success(request, "Patient créé avec succès!")
            return redirect(f"/patient/{patient.id}/")

        return render(
            request,
            "patients/patient_create.html",
            {"errors": serializer.errors, "form_data": request.POST},
        )

    def patient_detail(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Affiche les détails d'un patient.

        Args:
            request: La requête HTTP.
            pk: L'identifiant primaire du patient.

        Returns
        -------
            HttpResponse: Réponse HTTP avec les détails du patient.

            - 200 OK avec les données du patient
            - 404 Not Found si patient non trouvé
        """
        patient = get_object_or_404(Patient, pk=pk)
        serializer = PatientFHIRSerializer(patient)
        data = self.extract_patient_extensions(serializer.data)
        return render(request, "patients/patient_detail.html", {"patient": data})

    def edit_patient_form(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Affiche le formulaire d'édition d'un patient.

        Args:
            request: La requête HTTP.
            pk: L'identifiant primaire du patient à éditer.

        Returns
        -------
            HttpResponse: Réponse HTTP avec le formulaire pré-rempli.

            - 200 OK avec le formulaire
            - 404 Not Found si patient non trouvé
        """
        patient = get_object_or_404(Patient, pk=pk)
        serializer = PatientFHIRSerializer(patient)
        data = self.extract_patient_extensions(serializer.data)
        return render(request, "patients/patient_update.html", {"patient": data})

    def handle_edit_patient(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Traite la mise à jour d'un patient via formulaire.

        Args:
            request: La requête HTTP contenant les données du formulaire.
            pk: L'identifiant primaire du patient à mettre à jour.

        Returns
        -------
            HttpResponse: Réponse HTTP avec le résultat de l'opération.

            - 302 Redirect vers la page du patient si succès
            - 400 Bad Request avec les erreurs si échec
            - 404 Not Found si patient non trouvé
        """
        patient = get_object_or_404(Patient, pk=pk)
        fhir_data = self.form_to_fhir(request.POST, patient.id)
        serializer = PatientFHIRSerializer(patient, data=fhir_data)

        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Patient mis à jour avec succès")
            return redirect(f"/patient/{pk}/")

        return render(
            request, "patients/patient_update.html", {"patient": patient, "errors": serializer.errors}, status=400
        )

    def handle_delete_patient(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Traite la suppression d'un patient.

        Args:
            request: La requête HTTP.
            pk: L'identifiant primaire du patient à supprimer.

        Returns
        -------
            HttpResponse: Réponse HTTP avec le résultat de l'opération.

            - 302 Redirect vers la liste des patients si succès
            - 404 Not Found si patient non trouvé
        """
        if request.method == "POST":
            patient = get_object_or_404(Patient, pk=pk)
            patient.delete()
            messages.success(request, "Patient supprimé avec succès")
            return redirect("patients:patient-list")
        return redirect("patients:patient-detail", pk=pk)
