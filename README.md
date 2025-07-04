![Static Badge](/static/badges/Python.svg)
![Static Badge](/static/badges/Django.svg)   
![Static Badge](/static/badges/Django_REST_Framework.svg)   
![Static Badge](/static/badges/Postman.svg) ➔ [Documentation Postman du projet CODOC FHIR](https://documenter.getpostman.com/view/26427645/2sB34ZsQWs)    

[<img src="https://run.pstmn.io/button.svg" alt="Run In Postman" style="vertical-align: middle; width: 128px; height: 32px;">](https://god.gw.postman.com/run-collection/26427645-91986fa4-277e-4253-8e86-63a5c2846265?action=collection%2Ffork&source=rip_markdown&collection-url=entityId%3D26427645-91986fa4-277e-4253-8e86-63a5c2846265%26entityType%3Dcollection%26workspaceId%3D52058af2-40c1-4e2a-8cd8-a43b62cb634e)   

<div id="top"></div>

## Menu   

1. **[Informations générales](#informations-générales)**   
2. **[Fonctionnalités](#fonctionnalités)**   
3. **[Liste pré-requis](#liste-pre-requis)**   
4. **[Création environnement](#creation-environnement)**   
5. **[Activation environnement](#activation-environnement)**   
6. **[Installation des librairies](#installation-librairies)**   
7. **[Administration opérations CRUD et gestionnaires de commmandes](#administration-bdd)**   
8. **[Interface de l'application](#interface-application)**   
9. **[Exécution de l'application](#execution-application)**      
10. **[Rapport avec le fichier pre_commit.sh](#rapport-pre_commit)**   
11. **[Informations importantes sur les différents fichiers et dossiers](#informations-importantes)**   
12. **[Auteur et contact](#auteur-contact)**   


<div id="informations-générales"></div>

### API Patients conforme FHIR (Django + DRF)

#### Description

- Ce projet implémente une **API RESTful** pour la gestion des dossiers patients, conforme au standard **HL7 FHIR**.   
- En utilisant **Django et Django REST Framework** (DRF).   
- L’**API** permet de créer, lire, mettre à jour et supprimer des patients.
- En respectant la structure et le comportement des ressources **FHIR Patient**.
- La documentation est disponible à cette adresse➔ [HL7 FHIR](https://hl7.org/fhir/)    

--------------------------------------------------------------------------------------------------------------------------------

<div id="fonctionnalités"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Fonctionnalités   

- **CRUD** complet pour les ressources Patient **FHIR** (``POST``, ``GET``, ``PUT``, ``DELETE``)
- Conformité avec les spécifications **FHIR** pour :
  - La structure des données (JSON)
  - Les opérations **HTTP**
  - Les en-têtes spécifiques
- Gestion des erreurs avec codes **HTTP** standard  

#### Architecture et Endpoints

Le projet sépare clairement les interfaces Web et **API** **REST** dans des fichiers distincts. :

- `web_views.py` ➔ ([web_views.py](apps/patients/web_views.py)) : Gère l'interface HTML traditionnelle (rendue côté serveur)
- `api_views.py` ➔ ([api_views.py](apps/patients/api_views.py)) : Gère les endpoints **API** **RESTful** conformes à **FHIR**

#### Interface Web (HTML)

| Méthode | Endpoint                     | Description                         | Template                        |
|---------|------------------------------|-------------------------------------|---------------------------------|
| GET     | `/patient/`                  | Liste paginée des patients          | `patient_list.html`             |
| GET     | `/patient/{id}/`             | Détails d'un patient                | `patient_detail.html`           |
| GET/POST| `/patient/new/`              | Formulaire de création              | `patient_create.html`           |
| GET/PUT | `/patient/{id}/edit/`        | Formulaire d'édition                | `patient_update.html`           |
| DELETE  | `/patient/{id}/`             | Suppression d'un patient            | (Redirection vers la liste)     |

#### API REST (FHIR JSON)

| Méthode | Endpoint                     | Description                         | Conformité FHIR                 |
|---------|------------------------------|-------------------------------------|---------------------------------|
| GET     | `/api/patient/`              | Liste des patients (JSON)           | Bundle FHIR                     |
| GET     | `/api/patient/{id}/`         | Détails d'un patient (JSON)         | Resource Patient FHIR           |
| POST    | `/api/patient/`              | Création d'un patient               | Supporte `If-None-Exist`        |
| PUT     | `/api/patient/{id}/`         | Mise à jour complète                | Version-aware updates           |
| DELETE  | `/api/patient/{id}/`         | Suppression (retourne 204)          | Logical delete supporté         |

- Tester et accessible via **Postman** cette **API** permet d’interagir avec les ressources **Patient** au format JSON en respectant la norme **FHIR**.
- Une documentation du projet est disponible sur **Postman** ➔ [Documentation Postman du projet CODOC FHIR](https://documenter.getpostman.com/view/26427645/2sB34ZsQWs)   

- Import et exécute la collection dans votre propre espace de travail **Postman** ➔ [<img src="https://run.pstmn.io/button.svg" alt="Run In Postman" style="vertical-align: middle; width: 128px; height: 32px;">](https://god.gw.postman.com/run-collection/26427645-91986fa4-277e-4253-8e86-63a5c2846265?action=collection%2Ffork&source=rip_markdown&collection-url=entityId%3D26427645-91986fa4-277e-4253-8e86-63a5c2846265%26entityType%3Dcollection%26workspaceId%3D52058af2-40c1-4e2a-8cd8-a43b62cb634e)

#### Fonctionnalités communes

- **Validation FHIR** intégrée dans les deux interfaces
- **Sérialisation/désérialisation** via ``serializers.py`` ➔ ([serializers.py](apps/patients/serializers.py)) partagé.

#### En-têtes FHIR supportés

- `If-None-Exist` : Empêche la création de doublons
- `Prefer` : 
  - `return=representation` : Retourne la ressource complète après opération
  - `return=minimal` : Retourne seulement les métadonnées

>_**Note :** Testé sous **Windows 11** Professionnel - **Python** 3.12.0_   

--------------------------------------------------------------------------------------------------------------------------------

<div id="liste-pre-requis"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Liste pré-requis   

Application conçue avec les technologies suivantes :   

- **Python** v3.12.0 choisissez la version adaptée à votre ordinateur et système.   
- **Python** est disponible à l'adresse suivante ➔ https://www.python.org/downloads/   
- **Django** version 5.0.7 ➔ [Documentation Django](https://docs.djangoproject.com/en/5.0/)    
- **Django REST Framework** version 3.15.2 ➔ [Documentation Django REST Framework](https://www.django-rest-framework.org/)    
- **Windows 11** Professionnel   
  &nbsp;   

| - Les scripts **Python** s'exécutent depuis un terminal.                                            |
------------------------------------------------------------------------------------------------------|
| - Pour ouvrir un terminal sur **Windows**, pressez la touche ```windows + r``` et entrez ```cmd```. |
| - Sur **Mac**, pressez la touche ```command + espace``` et entrez ```terminal```.                   |
| - Sur **Linux**, vous pouvez ouvrir un terminal en pressant les touches ```Ctrl + Alt + T```.       |

--------------------------------------------------------------------------------------------------------------------------------

<div id="creation-environnement"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Création de l'environnement virtuel   

- Installer une version de **Python** compatible pour votre ordinateur.   
- Une fois installer ouvrer le **CMD** (terminal) placer vous dans le dossier principal **(dossier racine)**.   

Taper dans votre terminal :    

```bash   
$ python -m venv env
```   

>_**Note :** Un répertoire appelé **env** doit être créé._   

--------------------------------------------------------------------------------------------------------------------------------

<div id="activation-environnement"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Activation de l'environnement virtuel   

- Placez-vous avec le terminal dans le dossier principale **(dossier racine)**.   

Pour activer l'environnement virtuel créé, il vous suffit de taper dans votre terminal :   

```bash
$ env\Scripts\activate.bat
```
- Ce qui ajoutera à chaque début de ligne de commande de votre terminal ``(env)`` :   
>_**Note :** Pour désactiver l'environnement virtuel, il suffit de taper dans votre terminal :_  

```bash
$ deactivate
```
--------------------------------------------------------------------------------------------------------------------------------

<div id="installation-librairies"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Installation des librairies   

- Le programme utilise plusieurs librairies externes et modules de **Python**, qui sont répertoriés dans le fichier ``requirements.txt``.   
- Placez-vous dans le dossier où se trouve le fichier ``requirements.txt`` à la racine du projet, l'environnement virtuel doit être activé.   
- Pour faire fonctionner l'application, il vous faudra installer les librairies requises.   
- À l'aide des fichiers ``requirements.txt`` et ``requirements_dev.txt`` mis à disposition.   

Taper dans votre terminal la commande :   

```bash
$ pip install -r requirements.txt
```

```bash
$ pip install -r requirements_dev.txt
```

#### Installation des données

- Créer une base de données **SQLite** locale avec la commande :   

```bash
$ python manage.py migrate
```

- Charger les données avec la commande :   

```bash
$ python manage.py loaddata patients/fixtures/patients.json
```

--------------------------------------------------------------------------------------------------------------------------------

<div id="administration-bdd"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Administration opérations CRUD et gestionnaire de commmandes   

La gestion des opérations **CRUD** peut se faire de plusieurs manières :   

- En utilisant l'interface web ➔ http://127.0.0.1:8000/Patient/   
- En utilisant des commandes dans Le shell **Django**   
- En utilisant le site d'administration de **Django** à l'adresse suivante ➔ http://127.0.0.1:8000/admin/   

##### Utilisateur enregistré dans la basse de données

| **Identifiant** | **Mot de passe** |
|-----------------|------------------|
|    Admin        |    Admin123      |

- Vous pouvez créer un utilisateur avec la commande :

```bash   
$ python manage.py createsuperuser
```   

--------------------------------------------------------------------------------------------------------------------------------

<div id="interface-application"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Interface de l'application     

L'interface de l'application fonctionne sur une page web.   

#### Affiche tous les patients.   

* Disponible à l'adresse ➔ http://127.0.0.1:8000/patient/   

![Display list patient](/static/img/screen_list_patients.png)   

#### Affiche les détails d'un patient.   

* Disponible à l'adresse ➔ http://127.0.0.1:8000/patient/id/   

![Display detail patient](/static/img/screen_details_patient.png)   

##### Création d'un patient.   

* Disponible à l'adresse ➔ http://127.0.0.1:8000/patient/new/ 

![Display create patient](/static/img/screen_create_patient.png)   


##### Mise à jour et suppression d'un patient.   

* Disponible à l'adresse ➔ http://127.0.0.1:8000/patient/edit/   

![Display edit patient](/static/img/screen_update_patient.png)   

--------------------------------------------------------------------------------------------------------------------------------

<div id="execution-application"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Exécution de l'application   

#### Utilisation de l'application.   

Lancement du serveur **Django**.   
- Placez-vous avec le terminal **CMD** dans le dossier principal.   
- Activer l'environnement virtuel et ensuite lancer le serveur **Django**.   

- Taper dans votre terminal la commande :   

```bash   
$ python manage.py runserver
```   

- Démarrer le serveur vous permet d'accéder à l'application **Django**.   
- Disponible à l'adresse suivante ➔ http://127.0.0.1:8000/Patient/   
- Permets d'utiliser les requêtes ``GET``, ``POST``, ``PUT``, ``DEL`` lors de l'utilisation de **Postman**.   

>_**Note navigateur :** Les tests ont était fait sur **Firefox** et **Google Chrome**._   

--------------------------------------------------------------------------------------------------------------------------------

<div id="rapport-pre_commit"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Rapport avec le script pre_commit.sh   

- Un script ``./bin/pre_commit.sh`` pour exécuter des vérifications de qualité du code (nécessite les dépendances de **requirements_dev.txt**).
- Dans le fichier ``pre_commit.sh si`` vous êtes sous Windows il faudra modifier dans les sections suivantes :

- Section **SWAGGER** (remplacer **python3** par **python**)

```bash
$ out=$(python3 manage.py spectacular --fail-on-warn &> /dev/null)
```

- Section **MIGRATIONS** (remplacer **python3** par **python**)

```bash
$ out=$(python3 manage.py makemigrations --check --dry-run --no-input &> /dev/null)
```

- Tapez dans votre terminal la commande : 

```bash
$ ./bin/pre_commit.sh
```

```bash   
Bubhux@TOTORO MINGW64 /d/CODOC-FHIR (development)
$ ./bin/pre_commit.sh
Formatting import with isort... 
Fixing D:\Test CODOC\CODOC-FHIRpps\patients\urls.py
Ok ✅

Formatting code with black...
All done! ✨ 🍰 ✨
19 files left unchanged.

Running flake8... Ok ✅ 
Running pydocstyle... Ok ✅ 
Running mypy... Ok ✅ 
Running bandit... Ok ✅ 
Checking for swagger errors / warnings.. Ok ✅ 
Checking for missing migrations... Ok ✅ 

✨ You can commit without any worry ✨
```   
- Ne renvoie aucune erreur.   
- Si vous souhaitez générer la documentation de l'API au format **OpenAPI 3.0**
- Avec **drf-spectacular** qui est un outil pour **Django REST Framework (DRF)**
- Tapez dans votre terminal la commande : 

```bash
$ python manage.py spectacular --file schema.yaml
```

- Génère un schéma **OpenAPI** (documentation structurée de l'API).
- Sauvegarde le schéma dans un fichier **YAML** ``(schema.yaml)``.

Ce fichier peut ensuite être utilisé pour :

- Générer une interface **Swagger/Redoc**.
- Importer dans des outils comme **Postman** ou **Insomnia**.

--------------------------------------------------------------------------------------------------------------------------------

<div id="informations-importantes"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Informations importantes sur les différents fichiers et dossiers   

#### Le dossier patients   

  - Contient les fichiers ``api_views.py`` ``web_views.py`` ``mixins.py`` ``serializers.py`` ``urls.py``.   
    - ``patients`` ➔ ([api_views.py](apps/patients/api_views.py))   
    - ``patients`` ➔ ([web_views.py](apps/patients/web_views.py))   
    - ``patients`` ➔ ([mixins.py](apps/patients/mixins.py))   
    - ``patients`` ➔ ([serializers.py](apps/patients/serializers.py))   
    - ``patients`` ➔ ([urls.py](apps/patients/urls.py))   

#### Le dossiers dwh_fhir   

  - Contient le fichier ``urls.py``.   
    - ``dwh_fhir`` ➔ ([urls.py](/dwh_fhir/urls.py))   

#### Le dossier templates   

  - Le dossier contient les templates ``patient_list.html`` ``patient_detail.html``  ``patient_create.html`` ``patient_update.html``
    - ``templates`` ➔ ([patient_list.html](apps/patients/templates/patients/patient_list.html))   
    - ``templates`` ➔ ([patient_detail.html](apps/patients/templates/patients/patient_detail.html))   
    - ``templates`` ➔ ([patient_create.html](apps/patients/templates/patients/patient_create.html))   
    - ``templates`` ➔ ([patient_update.html](apps/patients/templates/patients/patient_update.html))   

#### Le fichier schema.yaml

  - Le fichier ``schema.yaml`` qui contient un schéma **OpenAPI** (documentation structurée de votre API).  
    - ``schema.yaml`` ➔ ([schema.yaml](schema.yaml))   

#### Le dossier static   

  - Dossier qui contient les images et les badges nécessaire à l'application.   
    - ``static`` ➔ ([badges](static/badges))   
    - ``static`` ➔ ([img](static/img))   

#### Le fichier NOTES.md

  - Le fichier ``NOTES.md`` qui contient les informations complémentaires qui conerne le projet.  
    - ``NOTES.md`` ➔ ([NOTES.md](NOTES.md))  

--------------------------------------------------------------------------------------------------------------------------------

<div id="auteur-contact"></div>
<a href="#top" style="float: right;">Retour en haut 🡅</a>

### Auteur et contact   

Pour toute information supplémentaire, vous pouvez me contacter.   
**Bubhux Paindépice** ➔ bubhuxpaindepice@gmail.com   
