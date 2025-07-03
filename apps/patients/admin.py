# apps/patients/admin.py
from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour le modèle Patient.

    Définit les champs affichés dans la liste et les champs de recherche.
    """

    list_display = ("ipp", "last_name", "first_name", "birth_date")
    search_fields = ("ipp", "last_name", "first_name")
