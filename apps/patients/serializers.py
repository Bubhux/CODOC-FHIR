# app/patients/serializers.py
from rest_framework import serializers
from .models import Patient


class PatientFHIRSerializer(serializers.ModelSerializer):
    resourceType = serializers.CharField(default="Patient", read_only=True)
    id = serializers.CharField(source='pk', read_only=True)
    active = serializers.BooleanField(default=True, read_only=True)
    gender = serializers.SerializerMethodField()
    deceasedDateTime = serializers.DateTimeField(source='death_date', allow_null=True)
    birthDate = serializers.SerializerMethodField()

    # Ajout des champs comme SerializerMethodField pour les champs FHIR qui n'ont pas de correspondance directe
    identifier = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    telecom = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
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
            'generalPractitioner', 'managingOrganization', 'link'
        ]

    def get_birthDate(self, obj):
        if obj.birth_date:
            return obj.birth_date.date()  # Convert datetime to date
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
        return [{
            "use": "official",
            "family": obj.last_name,
            "given": [obj.first_name] if obj.first_name else [],
            "prefix": [],
            "suffix": []
        }]

    def get_telecom(self, obj):
        return [{
            "system": "phone",
            "value": obj.phone_number,
            "use": "home"
        }] if obj.phone_number else []

    def get_address(self, obj):
        if any([obj.residence_address, obj.residence_city, obj.residence_zip_code, obj.residence_country]):
            return [{
                "use": "home",
                "type": "both",
                "text": obj.residence_address,
                "line": [obj.residence_address] if obj.residence_address else [],
                "city": obj.residence_city,
                "district": "",
                "state": "",
                "postalCode": obj.residence_zip_code,
                "country": obj.residence_country,
                "period": {"start": ""},
                "extension": [{
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {
                            "url": "latitude",
                            "valueDecimal": float(obj.residence_latitude) if obj.residence_latitude else None
                        },
                        {
                            "url": "longitude",
                            "valueDecimal": float(obj.residence_longitude) if obj.residence_longitude else None
                        }
                    ]
                }] if obj.residence_latitude and obj.residence_longitude else []
            }]
        return []

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

        # Ajoutez les éléments FHIR qui nécessitent une structure particulière
        representation['meta'] = {
            "versionId": "1",
            "lastUpdated": instance.update_date.isoformat() if instance.update_date else None
        }

        if instance.birth_city or instance.birth_country:
            representation['extension'] = [{
                "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
                "valueAddress": {
                    "city": instance.birth_city,
                    "country": instance.birth_country,
                    "postalCode": instance.birth_zip_code,
                    "extension": [{
                        "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                        "extension": [
                            {
                                "url": "latitude",
                                "valueDecimal": instance.birth_latitude
                            },
                            {
                                "url": "longitude",
                                "valueDecimal": instance.birth_longitude
                            }
                        ]
                    }] if instance.birth_latitude is not None and instance.birth_longitude is not None else []
                }
            }]

        # Nettoyage des valeurs None
        def remove_none_values(data):
            if isinstance(data, dict):
                return {k: remove_none_values(v) for k, v in data.items() if v is not None}
            elif isinstance(data, list):
                return [remove_none_values(v) for v in data if v is not None]
            else:
                return data

        return remove_none_values(representation)

    def to_internal_value(self, data):
        fhir_data = data.copy()

        # Conversion des champs FHIR vers le modèle Django
        internal_value = {
            'ipp': next((id['value'] for id in fhir_data.get('identifier', [])
                        if id.get('system') == 'urn:oid:1.2.250.1.213.1.4.8'), None),
            'last_name': fhir_data.get('name', [{}])[0].get('family') if fhir_data.get('name') else None,
            'first_name': fhir_data.get('name', [{}])[0].get('given', [None])[0] if fhir_data.get('name') else None,
            'birth_date': fhir_data.get('birthDate'),
            'sex': {'male': 'M', 'female': 'F', 'other': 'O'}.get(fhir_data.get('gender'), 'O'),
            'phone_number': next((t['value'] for t in fhir_data.get('telecom', [])
                                if t.get('system') == 'phone'), None),
            'death_date': fhir_data.get('deceasedDateTime'),
        }

        # Gestion de l'adresse
        if fhir_data.get('address'):
            address = fhir_data['address'][0]
            internal_value.update({
                'residence_address': address.get('text') or (address.get('line', [None])[0]),
                'residence_city': address.get('city'),
                'residence_zip_code': address.get('postalCode'),
                'residence_country': address.get('country'),
            })

            # Gestion des coordonnées géographiques
            if address.get('extension'):
                for ext in address['extension']:
                    if ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/geolocation':
                        for sub_ext in ext.get('extension', []):
                            if sub_ext.get('url') == 'latitude':
                                internal_value['residence_latitude']=str(sub_ext.get('valueDecimal'))
                            elif sub_ext.get('url') == 'longitude':
                                internal_value['residence_longitude']=str(sub_ext.get('valueDecimal'))

        # Gestion du lieu de naissance
        if fhir_data.get('extension'):
            for ext in fhir_data['extension']:
                if ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/patient-birthPlace':
                    birth_place=ext.get('valueAddress', {})
                    internal_value.update({
                        'birth_city': birth_place.get('city'),
                        'birth_country': birth_place.get('country'),
                        'birth_zip_code': birth_place.get('postalCode'),
                    })
                    if birth_place.get('extension'):
                        for sub_ext in birth_place['extension']:
                            if sub_ext.get('url') == 'http://hl7.org/fhir/StructureDefinition/geolocation':
                                for sub_sub_ext in sub_ext.get('extension', []):
                                    if sub_sub_ext.get('url') == 'latitude':
                                        internal_value['birth_latitude']=sub_sub_ext.get('valueDecimal')
                                    elif sub_sub_ext.get('url') == 'longitude':
                                        internal_value['birth_longitude']=sub_sub_ext.get('valueDecimal')

        # Nettoyage des valeurs None
        return {k: v for k, v in internal_value.items() if v is not None}
