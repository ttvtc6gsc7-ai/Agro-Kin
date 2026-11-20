# RoboAgri-Kin — interface connectée

Lancer Django depuis `backend` avec `venv\Scripts\python.exe manage.py runserver`, puis ouvrir http://127.0.0.1:8000/. Les pages de supervision utilisent une session Django et le cookie CSRF ; elles ne fonctionnent pas en ouverture directe `file://`.

- `index.html` : nouvel accueil public.
- `dashboard.html` : tableau de bord après connexion.
- Parcelles, cultures, zones et missions : lectures et écritures persistantes dans le back-end.
- Robot, mesures, irrigation, incidents, historique et rapports : données du serveur actualisées toutes les dix secondes via `GET /api/supervision/` (opérateur ou administrateur).
- `js/api.js` : session, erreurs HTTP, CSRF et adaptation des données réelles.
- `js/app.js` : navigation, formulaires, tableaux et graphiques.
- Bibliothèques et images locales : aucun CDN nécessaire.
- « Documentation » : site explicatif du back-end à `/documentation/`.

La préparation d’une mission enregistre le robot choisi et ses étapes ordonnées dans une transaction unique, sans envoi automatique au robot. Les seuils, étalonnages et autorisations restent accessibles via l’administration ou les routes métier existantes.

Batterie, position, vitesse et température ne sont pas simulées. La connexion affichée est l’état déclaré en base : aucun heartbeat matériel n’est ajouté. Une irrigation autorisée ou envoyée n’est pas comptée comme exécutée sans confirmation.

L’ancien front-end est conservé dans `documentation/archives/frontend-avant-integration.zip`. Les guides et données de la maquette fournie sont dans `documentation/frontend/` et servent de référence historique.
