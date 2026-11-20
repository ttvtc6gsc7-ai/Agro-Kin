# Explication du backend RoboAgri-Kin

Ouvrir `index.html` dans un navigateur. Aucun serveur, installation ou accès Internet n’est nécessaire. Garder `style.css` et `script.js` dans le même dossier.

Le guide contient l’architecture, les parcours, les routes, les 12 modèles et tous leurs champs, les limites constatées, les contrôles exécutés et un explorateur du code backend. La recherche filtre les chapitres. Les liens Source ouvrent les fichiers intégrés. Le simulateur illustre la conversion d’humidité sans contacter le serveur. Le bouton Imprimer / PDF permet une copie complète via le navigateur.

## Partage

Pour préparer un dépôt de documentation, copier uniquement ce dossier dans un dépôt dédié. `index.html`, `style.css` et `script.js` suffisent au site ; `build.py` permet sa régénération depuis le projet source et n’est pas nécessaire à la consultation. Le dossier ne contient aucune copie de la base ni de secrets réels. Il contient toutefois du code source et des constats sur l’architecture : choisir la visibilité du dépôt selon les règles de l’équipe.

Un hébergement statique tel que GitHub Pages peut servir ces trois fichiers avec `index.html` à la racine publiée. Aucun dépôt, déploiement ou lien public n’a été créé automatiquement. Pour un partage local, envoyer le dossier complet sous forme d’archive.

## Mise à jour

Depuis la racine du projet :

```powershell
.\backend\venv\Scripts\python.exe '.\documentation\backend\build.py'
```

Le générateur lit les sources et les métadonnées de SQLite en lecture seule, masque la clé Django dans l’explorateur et écrit `index.html`. Il ne modifie ni les modèles, ni les migrations, ni les données. Les chapitres explicatifs et le bilan de tests sont éditoriaux : les relire et les actualiser après une évolution du backend. La date du guide est celle de l’analyse initiale, pas une horloge automatique de fraîcheur.


Le site est également accessible depuis l’application, rubrique Documentation (`/documentation/`), après connexion. La version initiale du dossier « Explication Backend » est conservée à sa place ; cette copie intégrée est la version à maintenir.
