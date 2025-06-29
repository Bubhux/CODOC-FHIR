# app/patients/serializers.py
from rest_framework import serializers
from .models import Patient


class PatientFHIRSerializer(serializers.ModelSerializer):
    resourceType = serializers.CharField(default="Patient", read_only=True)
    id = serializers.CharField(source='pk', read_only=True)
    active = serializers.BooleanField(default=True, read_only=True)
    gender = serializers.SerializerMethodField()
    deceasedDateTime = serializers.DateTimeField(source='death_date', allow_null=True)
    birthDate = serializers.DateField(source='birth_date', allow_null=True)
    maritalStatus = serializers.SerializerMethodField()
    multipleBirthBoolean = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'resourceType', 'id', 'identifier', 'active', 'name', 'telecom',
            'gender', 'birthDate', 'deceasedDateTime', 'address', 'maritalStatus',
            'multipleBirthBoolean', 'photo', 'contact', 'communication',
            'generalPractitioner', 'managingOrganization', 'link'
        ]

    def get_gender(self, obj):
        gender_mapping = {
            'M': 'male',
            'F': 'female',
            'O': 'other',
            None: 'unknown'
        }
        return gender_mapping.get(obj.sex, 'unknown')

    def get_maritalStatus(self, obj):
        # Le modèle ne contient pas cette information, donc on retourne None
        return None

    def get_multipleBirthBoolean(self, obj):
        # Le modèle ne contient pas cette information, donc on retourne None
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Construction de la structure FHIR complète
        fhir_patient = {
            "resourceType": "Patient",
            "id": str(instance.pk),
            "meta": {
                "versionId": "1",
                "lastUpdated": instance.update_date.isoformat() if instance.update_date else None
            },
            "identifier": [{
                "system": "urn:oid:1.2.250.1.213.1.4.8",  # OID français pour le numéro IPP
                "value": instance.ipp
            }],
            "active": True,  # Par défaut, on considère le patient comme actif
            "name": [{
                "use": "official",
                "family": instance.last_name,
                "given": [instance.first_name] if instance.first_name else [],
                "prefix": [],
                "suffix": []
            }],
            "telecom": [{
                "system": "phone",
                "value": instance.phone_number,
                "use": "home"
            }] if instance.phone_number else [],
            "gender": self.get_gender(instance),
            "birthDate": instance.birth_date.date().isoformat() if instance.birth_date else None,
            "deceasedDateTime": instance.death_date.isoformat() if instance.death_date else None,
            "address": [{
                "use": "home",
                "type": "both",
                "text": instance.residence_address,
                "line": [instance.residence_address] if instance.residence_address else [],
                "city": instance.residence_city,
                "district": "",
                "state": "",
                "postalCode": instance.residence_zip_code,
                "country": instance.residence_country,
                "period": {
                    "start": ""
                },
                "extension": [{
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {
                            "url": "latitude",
                            "valueDecimal": float(instance.residence_latitude) if instance.residence_latitude else None
                        },
                        {
                            "url": "longitude",
                            "valueDecimal": float(instance.residence_longitude) if instance.residence_longitude else None
                        }
                    ]
                }] if instance.residence_latitude and instance.residence_longitude else []
            }] if any([instance.residence_address, instance.residence_city,
                       instance.residence_zip_code, instance.residence_country]) else [],
            "extension": [{
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
            }] if instance.birth_city or instance.birth_country else []
        }

        # Nettoyage des valeurs None
        def remove_none_values(data):
            if isinstance(data, dict):
                return {k: remove_none_values(v) for k, v in data.items() if v is not None}
            elif isinstance(data, list):
                return [remove_none_values(v) for v in data if v is not None]
            else:
                return data

        return remove_none_values(fhir_patient)

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
