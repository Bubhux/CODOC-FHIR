# apps/patients/views.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast

from .models import Patient


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
