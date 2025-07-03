# app/patients/serializers.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import localtime, make_aware
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Patient


class PatientFHIRSerializer(serializers.ModelSerializer):
    """Sérialiseur pour transformer les données Patient au format FHIR.

    Ce sérialiseur convertit les données du modèle Patient Django en ressource FHIR Patient,
    conformément au standard HL7 FHIR STU3/R4.
    """

    resourceType = serializers.CharField(default="Patient", read_only=True)
    id = serializers.CharField(source="pk", read_only=True)
    active = serializers.BooleanField(default=True, read_only=True)
    gender = serializers.SerializerMethodField()
    birthDate = serializers.SerializerMethodField()
    deceasedDateTime = serializers.SerializerMethodField()

    # Champs FHIR complexes
    identifier = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    telecom = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()

    # Champs FHIR non implémentés (toujours null)
    maritalStatus = serializers.SerializerMethodField()
    multipleBirthBoolean = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    communication = serializers.SerializerMethodField()
    generalPractitioner = serializers.SerializerMethodField()
    managingOrganization = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    class Meta:
        """Configuration Meta du sérialiseur."""

        model = Patient
        fields = [
            "resourceType",
            "id",
            "identifier",
            "active",
            "name",
            "telecom",
            "gender",
            "birthDate",
            "deceasedDateTime",
            "address",
            "maritalStatus",
            "multipleBirthBoolean",
            "photo",
            "contact",
            "communication",
            "generalPractitioner",
            "managingOrganization",
            "link",
            "extension",
        ]

    def get_birthDate(self, obj: Patient) -> Optional[str]:
        """Récupère la date de naissance au format FHIR (YYYY-MM-DD).

        Args:
            obj: Instance du modèle Patient

        Returns
        -------
        Optional[str]
            Date formatée en YYYY-MM-DD ou None si non définie
        """
        if obj.birth_date:
            return obj.birth_date.strftime("%Y-%m-%d")
        return None

    def get_gender(self, obj: Patient) -> str:
        """Convertit le sexe du patient en code FHIR.

        Args:
            obj: Instance du modèle Patient

        Returns
        -------
        str
            Code FHIR parmi ('male', 'female', 'other', 'unknown')
        """
        gender_mapping = {"M": "male", "F": "female", "O": "other", None: "unknown"}
        return gender_mapping.get(obj.sex, "unknown")

    def get_identifier(self, obj: Patient) -> List[Dict[str, str]]:
        """Génère l'identifiant FHIR du patient (IPP).

        Args:
            obj: Instance du modèle Patient

        Returns
        -------
        list
            Liste contenant un dictionnaire avec le système et la valeur IPP
        """
        return [{"system": "urn:oid:1.2.250.1.213.1.4.8", "value": obj.ipp}]

    def get_name(self, obj: Patient) -> List[Dict[str, Any]]:
        """Construit le nom du patient au format FHIR.

        Args:
            obj: Instance du modèle Patient

        Returns
        -------
        list
            Liste contenant un dictionnaire avec les composants du nom
        """
        name_data = {
            "use": "official",
            "family": obj.last_name,
            "given": [obj.first_name] if obj.first_name else [],
        }

        if obj.maiden_name:
            name_data["maiden"] = obj.maiden_name

        return [name_data]

    def get_telecom(self, obj: Patient) -> List[Dict[str, str]]:
        """Récupère les coordonnées de contact au format FHIR.

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        List[Dict[str, str]]
            Liste des moyens de contact (téléphone, email)
        """
        telecom = []
        if obj.phone_number:
            telecom.append({"system": "phone", "value": obj.phone_number, "use": "home"})
        return telecom

    def get_address(self, obj: Patient) -> List[Dict[str, Any]]:
        """Construit l'adresse du patient au format FHIR.

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        List[Dict[str, Any]]
            Liste contenant un dictionnaire avec les composants de l'adresse
        """
        if not any([obj.residence_address, obj.residence_city, obj.residence_zip_code, obj.residence_country]):
            return []

        address = {
            "use": "home",
            "type": "both",
            "line": [obj.residence_address] if obj.residence_address else [],
            "city": obj.residence_city,
            "postalCode": obj.residence_zip_code,
            "country": obj.residence_country,
        }

        # Ajout des coordonnées géographiques si disponibles
        if obj.residence_latitude and obj.residence_longitude:
            address["extension"] = [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {"url": "latitude", "valueDecimal": float(obj.residence_latitude)},
                        {"url": "longitude", "valueDecimal": float(obj.residence_longitude)},
                    ],
                }
            ]

        return [address]

    def get_extension(self, obj: Patient) -> Optional[List[Dict[str, Any]]]:
        """Génère les extensions FHIR personnalisées.

        Args:
            obj: Instance du modèle Patient

        Returns
        -------
        Optional[List[Dict[str, Any]]]
            Liste des extensions FHIR ou None si aucune extension
        """
        extensions: List[Dict[str, Any]] = []

        # Extension pour le lieu de naissance
        if any([obj.birth_city, obj.birth_country, obj.birth_zip_code]):
            value_address: Dict[str, Any] = {
                "city": obj.birth_city,
                "postalCode": obj.birth_zip_code,
                "country": obj.birth_country,
            }

            # Ajout des coordonnées géographiques de naissance si disponibles
            if obj.birth_latitude is not None and obj.birth_longitude is not None:
                value_address["extension"] = [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                        "extension": [
                            {"url": "latitude", "valueDecimal": float(obj.birth_latitude)},
                            {"url": "longitude", "valueDecimal": float(obj.birth_longitude)},
                        ],
                    }
                ]

            birth_place: Dict[str, Any] = {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
                "valueAddress": value_address,
            }

            extensions.append(birth_place)

        # Extension pour la date de décès
        if obj.death_date:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-deathDate",
                    "valueDateTime": obj.death_date.isoformat(),
                }
            )

        # Extension pour le code de décès
        if obj.death_code:
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-deathCause",
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "urn:oid:1.2.250.1.213.1.4.5.2",
                                "code": obj.death_code,
                            }
                        ]
                    },
                }
            )

        return extensions if extensions else None

    # Méthodes pour les champs non implémentés (toujours null)
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_maritalStatus(self, obj: Patient) -> None:
        """Méthode pour le statut marital (non implémentée).

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        None
            Toujours None car non implémenté
        """
        return None

    @extend_schema_field(serializers.BooleanField(allow_null=True))
    def get_multipleBirthBoolean(self, obj: Patient) -> None:
        """Méthode pour les naissances multiples (non implémentée).

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        None
            Toujours None car non implémenté
        """
        return None

    @extend_schema_field(serializers.ImageField(allow_null=True))
    def get_photo(self, obj: Patient) -> None:
        """Méthode pour la photo du patient (non implémentée).

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        None
            Toujours None car non implémenté
        """
        return None

    def get_contact(self, obj: Patient) -> List[Any]:
        """Méthode pour les contacts (non implémentée).

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        List[Any]
            Liste vide car non implémenté
        """
        return []

    def get_communication(self, obj: Patient) -> List[Any]:
        """Méthode pour les préférences de communication (non implémentée).

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        List[Any]
            Liste vide car non implémenté
        """
        return []

    def get_generalPractitioner(self, obj: Patient) -> List[Any]:
        """Méthode pour le médecin traitant (non implémentée).

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        List[Any]
            Liste vide car non implémenté
        """
        return []

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_managingOrganization(self, obj: Patient) -> None:
        """Méthode pour l'organisation responsable (non implémentée).

        Returns
        -------
            None
        """
        return None

    def get_link(self, obj: Patient) -> List[Any]:
        """Méthode pour les liens vers autres ressources (non implémentée).

        Args
        ----
        obj : Patient
            Instance du modèle Patient

        Returns
        -------
        List[Any]
            Liste vide car non implémenté
        """
        return []

    def to_representation(self, instance: Patient) -> Dict[str, Any]:
        """Surcharge la méthode de sérialisation pour ajouter des métadonnées.

        Args:
            instance: Instance du modèle Patient

        Returns
        -------
        Dict[str, Any]
            Représentation FHIR complète du patient
        """
        representation = super().to_representation(instance)

        if instance.update_date:
            # si timezone aware, localize en local
            last_updated_dt = localtime(instance.update_date)
            last_updated_str = last_updated_dt.strftime("%d/%m/%Y à %H:%M")
        else:
            last_updated_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

        representation["meta"] = {"versionId": "1", "lastUpdated": last_updated_str}

        # Nettoyage des valeurs None
        def clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
            """Fonction utilitaire pour nettoyer les données None/vides.

            Args:
                data: Données à nettoyer (doit être un dictionnaire)

            Returns
            -------
            Dict[str, Any]
                Données nettoyées
            """
            if isinstance(data, dict):
                return {k: clean_data(v) for k, v in data.items() if v is not None and v != []}
            elif isinstance(data, list):
                return [clean_data(v) for v in data if v is not None]
            else:
                return data

        cleaned = clean_data(representation)
        if not isinstance(cleaned, dict):
            raise ValueError("La représentation nettoyée doit être un dictionnaire")
        return cleaned

    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Convertit une chaîne de date en objet date avec fuseau horaire.

        Args:
            date_str: Chaîne de date au format YYYY-MM-DD

        Returns
        -------
        Optional[datetime]
            Objet date ou None si conversion impossible
        """
        if not date_str:
            return None
        try:
            date = parse_date(date_str) or datetime.strptime(date_str, "%Y-%m-%d").date()
            return make_aware(datetime.combine(date, datetime.min.time()))
        except (ValueError, TypeError, AttributeError):
            return None

    def parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Convertit une chaîne datetime en objet datetime avec fuseau horaire.

        Args:
            datetime_str: Chaîne datetime au format ISO

        Returns
        -------
        Optional[datetime]
            Objet datetime ou None si conversion impossible
        """
        if not datetime_str:
            return None
        try:
            dt = parse_datetime(datetime_str) or datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
            return make_aware(dt) if dt else None
        except (ValueError, TypeError, AttributeError):
            return None

    def extract_death_date(self, extensions: Optional[List[Dict[str, Any]]]) -> Optional[str]:
        """Extrait la date de décès des extensions FHIR.

        Args:
            extensions: Liste des extensions FHIR

        Returns
        -------
        Optional[str]
            Date de décès ou None si non trouvée
        """
        if not extensions:
            return None
        for ext in extensions:
            if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/patient-deathDate":
                return ext.get("valueDateTime")
        return None

    def get_deceasedDateTime(self, obj: Patient) -> Optional[str]:
        """Récupère la date de décès au format FHIR.

        Args:
            obj: Instance du modèle Patient

        Returns
        -------
        Optional[str]
            Date formatée ou None si non définie
        """
        if isinstance(obj.death_date, str):
            return obj.death_date
        elif obj.death_date:
            return obj.death_date.strftime("%d/%m/%Y à %H:%M")
        return None

    def to_internal_value(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convertit les données FHIR en valeurs internes pour le modèle.

        Args:
            data: Dictionnaire de données FHIR

        Returns
        -------
        Dict[str, Any]
            Dictionnaire de valeurs prêtes pour la création/mise à jour
        """
        internal_value = {
            "ipp": next(
                (id["value"] for id in data.get("identifier", []) if id.get("system") == "urn:oid:1.2.250.1.213.1.4.8"),
                None,
            ),
            "last_name": data.get("name", [{}])[0].get("family"),
            "first_name": data.get("name", [{}])[0].get("given", [None])[0],
            "maiden_name": data.get("name", [{}])[0].get("maiden"),
            "birth_date": self.parse_date(data.get("birthDate")),
            "sex": data.get("gender", "").upper() if isinstance(data.get("gender"), str) else "O",
            "phone_number": next((t["value"] for t in data.get("telecom", []) if t.get("system") == "phone"), None),
            "death_date": self.parse_datetime(
                data.get("deceasedDateTime") or self.extract_death_date(data.get("extension"))
            ),
            "death_code": None,
        }

        # Traitement de l'adresse
        if data.get("address"):
            address = data["address"][0]
            internal_value.update(
                {
                    "residence_address": address.get("line", [None])[0],
                    "residence_city": address.get("city"),
                    "residence_zip_code": address.get("postalCode"),
                    "residence_country": address.get("country"),
                }
            )

        # Traitement des extensions
        if data.get("extension"):
            for ext in data["extension"]:
                # Coordonnées géographiques de résidence
                if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
                    for sub_ext in ext.get("extension", []):
                        if sub_ext.get("url") == "latitude":
                            internal_value["residence_latitude"] = str(sub_ext.get("valueDecimal")).replace(",", ".")
                        elif sub_ext.get("url") == "longitude":
                            internal_value["residence_longitude"] = str(sub_ext.get("valueDecimal")).replace(",", ".")

                # Lieu de naissance
                elif ext.get("url") == "http://hl7.org/fhir/StructureDefinition/patient-birthPlace":
                    birth_place = ext.get("valueAddress", {})
                    internal_value.update(
                        {
                            "birth_city": birth_place.get("city"),
                            "birth_zip_code": birth_place.get("postalCode"),
                            "birth_country": birth_place.get("country"),
                        }
                    )

                    # Coordonnées géographiques de naissance
                    if "extension" in ext:
                        for sub_ext in ext["extension"]:
                            if sub_ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
                                for geo_ext in sub_ext.get("extension", []):
                                    if geo_ext.get("url") == "latitude":
                                        internal_value["birth_latitude"] = str(geo_ext.get("valueDecimal")).replace(
                                            ",", "."
                                        )
                                    elif geo_ext.get("url") == "longitude":
                                        internal_value["birth_longitude"] = str(geo_ext.get("valueDecimal")).replace(
                                            ",", "."
                                        )

                # Cause de décès
                death_code_found = False
                if data.get("extension"):
                    for ext in data["extension"]:
                        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/patient-deathCause":
                            coding = ext.get("valueCodeableConcept", {}).get("coding", [{}])[0]
                            internal_value["death_code"] = coding.get("code")
                            death_code_found = True

                # Si aucune extension de décès trouvée, conserver None
                if not death_code_found:
                    internal_value["death_code"] = None

        return internal_value
