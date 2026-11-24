# RoboAgri-Kin

Application Django de supervision d’un robot agricole, avec le nouveau front-end HTML/CSS/JavaScript intégré : parcelles, cultures, zones, préparation de missions, mesures, irrigations, incidents et rapports.

## Démarrage (Windows PowerShell)

Depuis le dossier `backend`, pour une première installation :

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py creer_groupes
.\venv\Scripts\python.exe manage.py creer_compte operateur --password "VotreMotDePasse" --role Operateur
```

Démarrage habituel, toujours depuis `backend` :

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

Ouvrir http://127.0.0.1:8000/ puis « Découvrir l’application ». Utiliser un compte du groupe `Operateur`, `Administrateur` ou un superutilisateur pour la supervision. L’accueil est public ; les écrans de supervision demandent une connexion.

Créer un administrateur avec `venv\Scripts\python.exe manage.py createsuperuser`. L’administration `/admin/` permet notamment de configurer les robots, seuils et étalonnages.

## Données et connexion

Le navigateur utilise la session Django et le CSRF ; HTTP Basic et JWT ne sont pas activés. Le frontend et l’API partagent la même origine. Les bibliothèques et images sont locales.

`GET /api/supervision/` fournit les données réelles. Les formulaires écrivent dans `/api/cultures/`, `/api/parcelles/`, `/api/zones/` et `/api/missions/`. La création d’une mission accepte `robot`, `date_mission` et une liste `zones` ordonnée ; la mission et ses étapes sont enregistrées ensemble, sans envoi automatique au robot.

Les robots utilisent `X-Robot-Id` et `X-Robot-Token` sur les routes `/api/robot/`. L’intégration ne remplace pas le firmware et ne prouve pas une communication avec un robot physique. Les valeurs absentes ne sont pas inventées, et la connexion affichée vient de l’état déclaré en base.

## Documentation et sauvegarde

- Menu « Documentation » : site explicatif du back-end à `/documentation/`, après connexion.
- Sources du site : `documentation/backend/`. Régénération depuis la racine : `backend\venv\Scripts\python.exe documentation/backend/build.py`.
- Description de l’interface : `frontend/README.md`.
- Ancien front-end : `documentation/archives/frontend-avant-integration.zip`.
- Guides de la maquette fournie : `documentation/frontend/` (documents historiques).
- Le dossier original `Explication Backend/` est conservé.

## Contrôles

Depuis `backend` :

```powershell
.\venv\Scripts\python.exe manage.py test
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Les réglages actuels sont destinés au développement local. Les seuils, étalonnages, autorisations et envois restent disponibles via l’administration ou l’API métier existante. La nouvelle interface prépare les missions et consulte les opérations.

## Pilotage Wi-Fi de l’ESP32

Connectez le poste Django au Wi-Fi RoboAgri-Kin et ouvrez Pilotage du robot et autres avec un compte Operateur ou Administrateur. Vérifiez la connexion, puis maintenez une direction (souris, tactile ou touche Entrée/Espace sur le bouton). Relâcher demande l’arrêt. La cible est la carte du réseau local à 192.168.4.1, indépendamment du robot sélectionné dans la surveillance.

La carte doit fournir GET /status (JSON avec le champ texte etat) et GET /cmd?move=F|B|L|R|S. Le firmware doit arrêter les moteurs si les commandes cessent. Le ZIP fournit le protocole et la télécommande, sans sketch ni brochage.
