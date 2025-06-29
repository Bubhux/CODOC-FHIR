# apps/patients/models.py
from django.db import models


class Patient(models.Model):
    """Model representing all information related to a Patient."""

    id = models.BigAutoField(primary_key=True)
    ipp = models.CharField(max_length=30, unique=True)  # Identifier inside the hospital
    last_name = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateTimeField(blank=True, null=True)
    sex = models.CharField(max_length=2, blank=True, null=True)
    maiden_name = models.CharField(max_length=120, blank=True, null=True)
    residence_address = models.CharField(max_length=1000, blank=True, null=True)
    phone_number = models.CharField(max_length=1000, blank=True, null=True)
    residence_country = models.CharField(max_length=100, blank=True, null=True)
    residence_city = models.CharField(max_length=200, blank=True, null=True)
    residence_zip_code = models.CharField(max_length=30, blank=True, null=True)
    residence_latitude = models.CharField(max_length=300, blank=True, null=True)
    residence_longitude = models.CharField(max_length=300, blank=True, null=True)
    coordinates = models.CharField(max_length=200, blank=True, null=True)
    death_code = models.CharField(max_length=2, blank=True, null=True)
    death_date = models.DateTimeField(blank=True, null=True)
    birth_country = models.CharField(max_length=100, blank=True, null=True)
    birth_city = models.CharField(max_length=100, blank=True, null=True)
    birth_zip_code = models.CharField(max_length=10, blank=True, null=True)
    birth_latitude = models.FloatField(blank=True, null=True)
    birth_longitude = models.FloatField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "dwh_patient"
        indexes = (
            models.Index(fields=("last_name",)),
            models.Index(fields=("first_name",)),
            models.Index(fields=("maiden_name",)),
            models.Index(fields=("ipp",)),
        )
