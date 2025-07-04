# NOTE.md – Informations complémentaires

### 1. Hypothèses et choix de conception

##### 1.1 Utilisation de APIView plutôt que ViewSets

##### Pour la partie interface web

- ``app/patients/web_views.py`` ➔ ([web_views.py](apps/patients/web_views.py))
- Permet un contrôle précis sur les méthodes `**HTTP**` (``GET``, ``POST``, ``PUT``, ``DELETE``).
- Gère les vues HTML classiques accessibles via navigateur :

    - Affichage des patients, création, mise à jour, suppression
    - Personnalisation de la logique métier
    - Contrôle explicite sur chaque méthode HTT

##### Pour la partie API REST

- ``app/patients/api_views.py`` ➔ ([api_views.py](apps/patients/api_views.py))
- Fournit une **API RESTful** conforme à **FHIR** :

    - Exposition d’endpoints JSON (/api/patient/)
    - Gestion fine des méthodes HTTP
    - Réponses normalisées, adaptées aux clients API tester avec **Postman**.

##### 1.2 Mixin PatientMixin

- ``app/patients/mixins.py`` ➔ ([mixins.py](apps/patients/mixins.py))
- Centralise les méthodes de transformation et d’extraction des données au modèle **FHIR** **Patient**.
- Encourage la réutilisabilité et la séparation des responsabilités.
- Réduit la duplication de code dans les vues.

##### 1.3 Pagination

- La vue **PatientHTMLView** ``app/patients/web_views.py`` ➔ ([web_views.py](apps/patients/web_views.py)) utilise le Paginator de **Django** pour paginer les résultats.
- Facilite l'affichage et la gestion des données en cas de grands volumes.

##### 1.4 Utilisation de serializers.ModelSerializer

- ``app/patients/serializers.py`` ➔ ([serializers.py](apps/patients/serializers.py))
- Ce fichier contient le sérialiseur principal **PatientFHIRSerializer**
- Transforme une instance du modèle **Django** **Patient** en une ressource conforme au standard **FHIR**
- Format utilisé pour l'échange de données médicales.

------------------------------------------------------------------------------------------------------------------

### 2. Limitations actuelles

##### 2.1 Couverture **FHIR** incomplète

- Seuls les champs essentiels du modèle **Patient** **FHIR** sont supportés.
- Absence d’implémentation des opérations de recherche **FHIR** (search parameters).
- Gestion des erreurs non conforme à **FHIR** : pas d’**OperationOutcome** structuré.
- Headers **FHIR** non pris en charge (If-Modified-Since, etc.).

##### 2.2 Sécurité et contrôle d'accès

- Aucun mécanisme d’authentification ou de permissions.
- Pas de distinction entre les rôles (soignant, médecin, administratif).
- Aucune journalisation des accès (audit log absent).

##### 2.3 Tests et qualité logicielle

- Pas encore de tests unitaires ni de tests d’intégration.
- Couverture de code (ex : **Coverage**)
- Aucun test de performance (ex. **Locust**).
- Pas d’intégration avec une solution de monitoring (ex. **Sentry**).

------------------------------------------------------------------------------------------------------------------

### 3. Fonctionnalités à ajouter

##### 3.1 Recherche avancée

- Recherche par nom, prénom, ou IPP.
- Implémentation des paramètres de recherche **FHIR** (name, identifier, etc.).

##### 3.2 Sécurité et contrôle d'accès

- Ajout d’un système d’authentification (**OAuth2**, **JWT**).
- Gestion des rôles avec permissions différenciées.
- Journalisation des accès (audit trail complet).

##### 3.3 Améliorations **FHIR**

- Implémentation complète des **OperationOutcome**.
- Gestion des transactions et batches **FHIR**.
- Validation rigoureuse des données selon le standard **FHIR**.
- Extension du modèle **Patient** (champs supplémentaires : photo, communication, managingOrganization, etc.).

##### 3.4 Performance et monitoring

- Mise en place de tests de charge (ex : avec **Locust**).
- Intégration avec un outil de monitoring (ex : **Sentry**).

------------------------------------------------------------------------------------------------------------------

### 4. Évolutions techniques

- Conteneurisation avec **Docker**.
- Intégration continue et déploiement continu **CI/CD**.
- Déploiement du projet, notamment sur des plateformes comme **Heroku**, **Railway**, **Render**, ou **Vercel**.
