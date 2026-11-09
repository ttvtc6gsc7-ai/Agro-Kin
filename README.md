# RoboAgri-Kin — backend

Backend Django de supervision d’un robot agricole : planification de missions, mesures d’humidité, recommandations et contrôle d’irrigation. Le firmware ESP32 et le frontend ne font pas partie de ce backend.

## Architecture

- `parcelles` : cultures, parcelles, zones et seuils d’irrigation.
- `missions` : robots, missions et étapes.
- `mesures` : étalonnages et réception fiable des mesures.
- `irrigation` : recommandations, autorisations et résultats d’exécution.
- `incidents` : traçabilité des anomalies.
- `api` : API REST Django REST Framework, authentification et permissions.

Technologies : Python, Django 6.1, Django REST Framework 3.18 et SQLite pour le développement.

## Installation et démarrage (Windows PowerShell)

    cd backend
    py -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py creer_groupes
    python manage.py creer_compte operateur-demo --password "ChoisirUnMotDePasseFort" --role Operateur
    python manage.py runserver

Pour administrer les données à l’écran, créer d’abord un superutilisateur :

    python manage.py createsuperuser

Les variables de production (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` et la base de données) doivent être configurées hors du code avant un déploiement.

## Authentification et rôles

Les humains utilisent une session Django (admin) ou HTTP Basic Auth avec leur nom d’utilisateur et mot de passe. Il n’existe volontairement pas de jeton humain ni de route de connexion API dans cette version. Vérification : `GET /api/auth/me/`.

Les robots ne sont pas des utilisateurs Django. Chaque robot possède un identifiant UUID et un jeton distinct, stocké uniquement sous forme de hachage. Les requêtes robot portent les en-têtes `X-Robot-Id` et `X-Robot-Token`.

- `Administrateur` : gestion des robots et accès opérateur.
- `Operateur` : gestion agronomique, missions, étalonnages et autorisations d’irrigation.

## Endpoints principaux

Toutes les routes commencent par `/api/`.

| Domaine | Routes |
|---|---|
| Humain | `GET auth/me/`, `GET utilisateurs/`, `GET tableau-de-bord/`, `GET rapports/` |
| Parcelles | CRUD `cultures/`, `parcelles/`, `zones/`, `seuils/` |
| Robot et missions | CRUD `robots/`, `missions/`, `etapes/`; `POST missions/{id}/envoyer/` |
| Mesures | CRUD `etalonnages/`; `POST robot/mesures/` |
| Irrigation | `GET recommandations/`, `POST recommandations/{id}/autoriser/`, `GET irrigations/`, `POST irrigations/{id}/envoyer/` |
| Robot HTTP | `GET robot/missions/`, `GET robot/missions/{id}/etapes/`, `POST robot/missions/{id}/accuse/`, `GET robot/irrigations/`, `POST robot/irrigations/{id}/resultat/` |
| Incidents | `GET incidents/` |

## Exemples HTTP

Utilisateurs humains (Basic Auth) :

    curl -u operateur-demo:ChoisirUnMotDePasseFort http://127.0.0.1:8000/api/auth/me/
    curl -u operateur-demo:ChoisirUnMotDePasseFort -H "Content-Type: application/json" -d '{"nom":"Parcelle Nord","superficie":"2.50","localisation":"UCC"}' http://127.0.0.1:8000/api/parcelles/

Robot (remplacer les valeurs d’exemple) :

    curl -H "X-Robot-Id: UUID_DU_ROBOT" -H "X-Robot-Token: JETON_DU_ROBOT" http://127.0.0.1:8000/api/robot/missions/
    curl -X POST -H "Content-Type: application/json" -H "X-Robot-Id: UUID_DU_ROBOT" -H "X-Robot-Token: JETON_DU_ROBOT" -d '{"robot":1,"mission":1,"zone":1,"valeur_brute":"430","date_heure":"2026-11-09T10:00:00Z","message_id":"00000000-0000-0000-0000-000000000001"}' http://127.0.0.1:8000/api/robot/mesures/

Le jeton brut ne doit jamais être placé dans les journaux, le dépôt Git ou un fichier de configuration partagé.

## Tests et contrôles

    python manage.py test
    python manage.py check
    python manage.py makemigrations --check --dry-run

## Limites connues

- L’échange HTTP est testé au niveau Django, pas avec un ESP32 physique ni un réseau réel.
- SQLite et les réglages actuels sont destinés au développement.
- Les comptes utilisateurs sont gérés par Django ; une interface de connexion API dédiée n’est pas fournie.
