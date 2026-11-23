# Guide du code RoboAgri Kin

Ce guide décrit le frontend statique présent dans ce dossier. Le projet utilise
HTML, CSS et JavaScript, avec Bootstrap pour quelques composants et Plotly pour
les graphiques.

## 1. Démarrer l'application

Ouvrir `index.html` dans un navigateur pour voir la page d'accueil, puis choisir
**Découvrir l'application** pour ouvrir `dashboard.html`. Les autres pages
peuvent aussi être ouvertes directement. Une connexion Internet est nécessaire
pour charger Bootstrap, Bootstrap Icons et Plotly depuis leurs CDN. La
photographie de la page d'accueil est également hébergée par le site FarmDroid.

## 2. Organisation des fichiers

```text
index.html          Page d'accueil et présentation du projet
dashboard.html      Tableau de bord de supervision
parcelles.html      Gestion des parcelles et des zones
robot.html          État et télémétrie affichée du robot
mesures.html        Historique et graphiques des mesures
missions.html       Préparation locale et consultation des missions
irrigation.html     Seuils, recommandations et historique d'irrigation
incidents.html      Liste des incidents
historique.html     Journal filtrable des événements
rapports.html       Indicateurs et graphiques de synthèse
css/style.css       Palette, composants communs et adaptations responsive
js/landing.js       Menu mobile et animations de la page d'accueil
js/app.js           Navigation et logique d'affichage des pages de supervision
js/api.js           Accès aux données de démonstration et stockage local
js/data.js          Jeu de données fictives
README.md           Présentation courte et instructions générales
GUIDE_CODE.md       Explication détaillée des fichiers et des comportements
```

Les scripts et styles tiers minifiés sont chargés depuis des CDN dans les pages.
Ils ne sont pas du code métier RoboAgri Kin et ne sont donc pas commentés ici.

## 3. Page d'accueil

`index.html` est la page de présentation. Elle comprend :

- l'en-tête et ses liens vers les sections ou vers l'application ;
- le grand visuel avec une photographie FarmDroid et son crédit ;
- les quatre cartes de fonctionnalités, liées aux pages Mesures, Irrigation,
  Incidents et État du robot ;
- la section de mission et le pied de page.

Les liens **Découvrir l'application** pointent vers `dashboard.html`. Le tableau
de bord a été séparé de l'accueil pour préserver sa fonction de supervision.

`js/landing.js` ouvre et ferme le menu sur petit écran, met à jour l'année du
pied de page et révèle les sections au défilement avec `IntersectionObserver`.
Si cette API du navigateur n'est pas disponible, les sections sont affichées
directement.

## 4. Tableau de bord et navigation

Les pages de supervision chargent `js/data.js`, `js/api.js` puis `js/app.js`,
dans cet ordre : l'application utilise les données et les fonctions déclarées
par les deux premiers scripts.

Dans chaque page, `body[data-page]` identifie la vue à afficher. Le tableau de
bord utilise `data-page="index"` pour réutiliser le rendu correspondant dans
`app.js`; cela ne fait pas de `index.html` l'accueil du site.

`app.js` :

1. crée le menu latéral, le bouton de menu mobile et le pied de page ;
2. fournit les fonctions partagées de formatage (dates, états, tableaux,
   graphiques et messages) ;
3. lit les données via les fonctions de `api.js` ;
4. met à jour uniquement les éléments présents dans la page ouverte ;
5. rafraîchit les données affichées toutes les dix secondes ;
6. relie les formulaires de parcelles, zones, missions et irrigation.

Les liens du menu sont définis dans le tableau `MENU` en début de `app.js`.
Les identifiants HTML tels que `missionForm`, `graph` ou `historyTable` servent
de points de liaison entre chaque page et le JavaScript : si l'un de ces
identifiants change, son utilisation dans `app.js` doit être mise à jour aussi.

## 5. Données et stockage

### `js/data.js`

Ce fichier définit `DONNEES_DEMO`, les événements du robot, les parcelles et
leurs zones, les missions historiques et le dernier état illustratif du robot.
Il fournit aussi les valeurs de batterie, vitesse et position utilisées dans
l'interface. Ces informations sont fictives : aucune donnée de capteur ou de
robot physique n'est lue.

### `js/api.js`

Malgré son nom, ce fichier n'effectue actuellement aucun appel HTTP ou MQTT.
Ses fonctions `charger...` exposent les données de `data.js`, et les
modifications sont gardées dans le `localStorage` du navigateur :

- `roboagri.parcelles`
- `roboagri.zones`
- `roboagri.missions`
- `roboagri.configurations-irrigation`

Les données enregistrées restent sur le navigateur et son profil ; elles ne
sont pas envoyées à un serveur. Effacer les données du site/navigateur peut les
supprimer.

## 6. Fonctionnement des pages

| Page | Fichier HTML | Fonction principale |
|---|---|---|
| Accueil | `index.html` | Présenter RoboAgri Kin et orienter vers l'application |
| Tableau de bord | `dashboard.html` | Résumer état, mesures, parcelles, alertes et activités |
| Parcelles | `parcelles.html` | Ajouter/modifier parcelles et zones, voir l'humidité disponible |
| Robot | `robot.html` | Afficher état, batterie, position, vitesse, capteurs et incidents simulés |
| Mesures | `mesures.html` | Tracer humidité/température et lister les mesures reçues |
| Missions | `missions.html` | Choisir date/heure et ordre des zones, puis conserver le plan localement |
| Irrigation | `irrigation.html` | Consulter les arrosages et les mesures associées |
| Incidents | `incidents.html` | Lister obstacles, pertes de communication et erreurs de mesure |
| Historique | `historique.html` | Filtrer les événements par type, zone et date |
| Rapports | `rapports.html` | Calculer des indicateurs de mission, mesures, incidents et eau simulée |

Les graphiques sont rendus avec Plotly. Les pages qui n'en ont pas besoin
chargent tout de même la bibliothèque actuellement, par cohérence avec les
pages existantes.

## 7. Parcours des formulaires

- **Parcelles et zones** : `app.js` lit le formulaire, appelle
  `enregistrerParcelle` ou `enregistrerZone` dans `api.js`, puis redessine la
  liste.
- **Missions** : le formulaire transforme l'heure et la sélection ordonnée en
  objet mission. `enregistrerMission` crée un identifiant et ajoute cet objet
  dans `localStorage`.
- **Irrigation** : la page consulte les événements d'arrosage, leur durée,
  leur volume et les mesures associées. Elle ne configure pas de seuil et ne
  décide pas si un arrosage est nécessaire.

## 8. Limites importantes avant un branchement au robot

Le formulaire de mission **ne transmet pas de mission à un ESP32**. Il ne fait
qu'enregistrer une préparation dans le navigateur. Les missions, états,
mesures, incidents, niveau de batterie et événements d'irrigation affichés sont
simulés. Cette interface n'est pas connectée à l'ESP32 et n'envoie aucune
configuration de seuil.

Pour transformer cette démonstration en système connecté, il faudra définir une
interface réelle entre le navigateur et l'ESP32 (en général via un backend ou
un broker), un format de mission, les accusés de réception et états, ainsi que
les règles de sécurité et de validation côté contrôleur. Le capteur fournit la
mesure ; le contrôleur (par exemple l'ESP32) applique le seuil configuré dans
son programme et pilote la pompe. L'application pourra ensuite consulter les
mesures et résultats transmis, mais ne doit pas être considérée comme un
système de commande opérationnel.

## 9. Feuilles de style

`css/style.css` regroupe :

- les variables de palette dans `:root` ;
- les styles partagés de navigation, cartes, états, tableaux et formulaires ;
- la grille spécifique du tableau de bord ;
- les styles de la page d'accueil ;
- les animations, media queries et la règle
  `prefers-reduced-motion` pour limiter les mouvements si l'utilisateur le
  demande.

Les classes sont réutilisées entre les pages afin de garder une apparence
cohérente. Les couleurs de marque principales sont définies par `--vf`
(vert forêt) et `--vf2` (vert naturel).
