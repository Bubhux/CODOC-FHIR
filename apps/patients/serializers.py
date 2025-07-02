# app/patients/serializers.py
from rest_framework import serializers
from .models import Patient
from datetime import datetime
from django.utils.timezone import localtime, make_aware
from django.utils.dateparse import parse_date, parse_datetime


class PatientFHIRSerializer(serializers.ModelSerializer):
    resourceType = serializers.CharField(default="Patient", read_only=True)
    id = serializers.CharField(source='pk', read_only=True)
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
        model = Patient
        fields = [
            'resourceType', 'id', 'identifier', 'active', 'name', 'telecom',
            'gender', 'birthDate', 'deceasedDateTime', 'address', 'maritalStatus',
            'multipleBirthBoolean', 'photo', 'contact', 'communication',
            'generalPractitioner', 'managingOrganization', 'link', 'extension'
        ]

    def get_birthDate(self, obj):
        if obj.birth_date:
            return obj.birth_date.strftime('%Y-%m-%d')
        return None

    def get_gender(self, obj):
        gender_mapping = {
            'M': 'male',
            'F': 'female',
            'O': 'other',
            None: 'unknown'
        }
        return gender_mapping.get(obj.sex, 'unknown')

    def get_identifier(self, obj):
        return [{
            "system": "urn:oid:1.2.250.1.213.1.4.8",
            "value": obj.ipp
        }]

    def get_name(self, obj):
        name_data = {
            "use": "official",
            "family": obj.last_name,
            "given": [obj.first_name] if obj.first_name else [],
        }

        if obj.maiden_name:
            name_data["maiden"] = obj.maiden_name

        return [name_data]

    def get_telecom(self, obj):
        telecom = []
        if obj.phone_number:
            telecom.append({
                "system": "phone",
                "value": obj.phone_number,
                "use": "home"
            })
        return telecom

    def get_address(self, obj):
        if not any([obj.residence_address, obj.residence_city,
                   obj.residence_zip_code, obj.residence_country]):
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
            address["extension"] = [{
                "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                "extension": [
                    {
                        "url": "latitude",
                        "valueDecimal": float(obj.residence_latitude)
                    },
                    {
                        "url": "longitude",
                        "valueDecimal": float(obj.residence_longitude)
                    }
                ]
            }]

        return [address]

    def get_deceasedDateTime(self, obj):
        if obj.death_date:
            return obj.death_date.strftime('%d/%m/%Y à %H:%M')
        return None

    def get_extension(self, obj):
        extensions = []

        # Extension pour le lieu de naissance
        if any([obj.birth_city, obj.birth_country, obj.birth_zip_code]):
            birth_place = {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
                "valueAddress": {
                    "city": obj.birth_city,
                    "postalCode": obj.birth_zip_code,
                    "country": obj.birth_country,
                }
            }

            # Ajout des coordonnées géographiques de naissance si disponibles
            if obj.birth_latitude is not None and obj.birth_longitude is not None:
                birth_place["valueAddress"]["extension"] = [{
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {
                            "url": "latitude",
                            "valueDecimal": float(obj.birth_latitude)
                        },
                        {
                            "url": "longitude",
                            "valueDecimal": float(obj.birth_longitude)
                        }
                    ]
                }]

            extensions.append(birth_place)

        # Extension pour la date de décès
        if obj.death_date:
            extensions.append({
                "url": "http://hl7.org/fhir/StructureDefinition/patient-deathDate",
                "valueDateTime": obj.death_date.isoformat()
            })

        # Extension pour le code de décès
        if obj.death_code:
            extensions.append({
                "url": "http://hl7.org/fhir/StructureDefinition/patient-deathCause",
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "urn:oid:1.2.250.1.213.1.4.5.2",
                        "code": obj.death_code
                    }]
                }
            })

        return extensions if extensions else None

    # Méthodes pour les champs non implémentés (toujours null)
    def get_maritalStatus(self, obj):
        return None

    def get_multipleBirthBoolean(self, obj):
        return None

    def get_photo(self, obj):
        return None

    def get_contact(self, obj):
        return []

    def get_communication(self, obj):
        return []

    def get_generalPractitioner(self, obj):
        return []

    def get_managingOrganization(self, obj):
        return None

    def get_link(self, obj):
        return []

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.update_date:
            # si timezone aware, localize en local
            last_updated_dt = localtime(instance.update_date)
            last_updated_str = last_updated_dt.strftime('%d/%m/%Y à %H:%M')
        else:
            last_updated_str = datetime.now().strftime('%d/%m/%Y à %H:%M')

        representation['meta'] = {
            "versionId": "1",
            "lastUpdated": last_updated_str
        }

        # Nettoyage des valeurs None
        def clean_data(data):
            if isinstance(data, dict):
                return {k: clean_data(v) for k, v in data.items() if v is not None and v != []}
            elif isinstance(data, list):
                return [clean_data(v) for v in data if v is not None]
            else:
                return data

        return clean_data(representation)

    def parse_date(self, date_str):
        """Convertit une chaîne de date en objet date avec fuseau horaire"""
        if not date_str:
            return None
        try:
            date = parse_date(date_str) or datetime.strptime(date_str, '%Y-%m-%d').date()
            return make_aware(datetime.combine(date, datetime.min.time()))
        except (ValueError, TypeError, AttributeError):
            return None

    def parse_datetime(self, datetime_str):
        """Convertit une chaîne datetime en objet datetime avec fuseau horaire"""
        if not datetime_str:
            return None
        try:
            dt = parse_datetime(datetime_str) or datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
            return make_aware(dt) if dt else None
        except (ValueError, TypeError, AttributeError):
            return None

    def extract_death_date(self, extensions):
        """Extrait la date de décès des extensions FHIR"""
        if not extensions:
            return None
        for ext in extensions:
            if ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/patient-deathDate':
                return ext.get('valueDateTime')
        return None

    def get_deceasedDateTime(self, obj):
        if isinstance(obj.death_date, str):
            return obj.death_date
        elif obj.death_date:
            return obj.death_date.strftime('%d/%m/%Y à %H:%M')
        return None

    def to_internal_value(self, data):
        internal_value = {
            'ipp': next(
                (id['value'] for id in data.get('identifier', [])
                 if id.get('system') == 'urn:oid:1.2.250.1.213.1.4.8'),
                None
            ),
            'last_name': data.get('name', [{}])[0].get('family'),
            'first_name': data.get('name', [{}])[0].get('given', [None])[0],
            'maiden_name': data.get('name', [{}])[0].get('maiden'),
            'birth_date': self.parse_date(data.get('birthDate')),
            'sex': data.get('gender', '').upper() if isinstance(data.get('gender'), str) else 'O',
            'phone_number': next(
                (t['value'] for t in data.get('telecom', [])
                 if t.get('system') == 'phone'),
                None
            ),
            'death_date': self.parse_datetime(data.get('deceasedDateTime') or self.extract_death_date(data.get('extension'))),
            'death_code': None,
        }

        # Traitement de l'adresse
        if data.get('address'):
            address = data['address'][0]
            internal_value.update({
                'residence_address': address.get('line', [None])[0],
                'residence_city': address.get('city'),
                'residence_zip_code': address.get('postalCode'),
                'residence_country': address.get('country'),
            })

        # Traitement des extensions
        if data.get('extension'):
            for ext in data['extension']:
                # Coordonnées géographiques de résidence
                if ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/geolocation':
                    for sub_ext in ext.get('extension', []):
                        if sub_ext.get('url') == 'latitude':
                            internal_value['residence_latitude'] = str(sub_ext.get('valueDecimal')).replace(',', '.')
                        elif sub_ext.get('url') == 'longitude':
                            internal_value['residence_longitude'] = str(sub_ext.get('valueDecimal')).replace(',', '.')

                # Lieu de naissance
                elif ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/patient-birthPlace':
                    birth_place = ext.get('valueAddress', {})
                    internal_value.update({
                        'birth_city': birth_place.get('city'),
                        'birth_zip_code': birth_place.get('postalCode'),
                        'birth_country': birth_place.get('country'),
                    })

                    # Coordonnées géographiques de naissance
                    if 'extension' in ext:
                        for sub_ext in ext['extension']:
                            if sub_ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/geolocation':
                                for geo_ext in sub_ext.get('extension', []):
                                    if geo_ext.get('url') == 'latitude':
                                        internal_value['birth_latitude'] = str(geo_ext.get('valueDecimal')).replace(',', '.')
                                    elif geo_ext.get('url') == 'longitude':
                                        internal_value['birth_longitude'] = str(geo_ext.get('valueDecimal')).replace(',', '.')

                # Cause de décès
                if data.get('extension'):
                    for ext in data['extension']:
                        # Cause de décès
                        if ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/patient-deathCause':
                            coding = ext.get('valueCodeableConcept', {}).get('coding', [{}])[0]
                            internal_value['death_code'] = coding.get('code')
                        # Date de décès
                        elif ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/patient-deathDate':
                            internal_value['death_date'] = ext.get('valueDateTime')

        return {k: v for k, v in internal_value.items() if v is not None}
