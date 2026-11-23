# RoboAgri-Kin – Frontend

Frontend de démonstration du projet universitaire RoboAgri-Kin, réalisé en
HTML5, CSS3 et JavaScript, avec Bootstrap 5 et Plotly pour l'interface et les
graphiques. Ouvrir `index.html` pour la page d'accueil, puis choisir
« Découvrir l'application » pour accéder au tableau de bord `dashboard.html`.
La page d'accueil utilise une photographie distante du site FarmDroid ; les
bibliothèques Bootstrap, Bootstrap Icons et Plotly sont chargées depuis des CDN.

L'interface permet de gérer les parcelles et les zones, de préparer des missions
et de consulter les événements d'irrigation. Le seuil d'humidité relève du
contrôleur (par exemple l'ESP32), pas de cette interface. Aucune commande n'est
envoyée au robot. En mode démonstration, les écritures de gestion sont stockées
dans `localStorage` et ne sont pas transmises au robot ni à un serveur.

- `css/style.css` : charte visuelle, styles de l'application et mise en page responsive.
- `js/landing.js` : menu mobile et animations d'apparition de la page d'accueil.
- `js/data.js` : données de démonstration explicitement signalées dans l'interface.
- `js/api.js` : accès unique aux données de démonstration et stockage local des
  opérations de gestion, à remplacer par des appels au backend.
- `js/app.js` : navigation, affichage des pages, tableaux, graphiques et états;
  actualisation périodique toutes les 10 secondes.
- `GUIDE_CODE.md` : explication des fichiers, du parcours des données et des
  limites actuelles de la démonstration.
- `index.html` : page d'accueil RoboAgri Kin.
- `dashboard.html` : tableau de bord de supervision.
- Pages complémentaires : parcelles et zones, surveillance du robot, mesures,
  missions, irrigation, incidents, historique et rapports.

Les valeurs d'humidité sont présentées comme des valeurs brutes. Les données,
y compris les informations de batterie et d'état, sont fictives et servent à
la démonstration ; aucune connexion matérielle n'est revendiquée. Le seuil devra
être déterminé par étalonnage et essais, puis configuré dans le contrôleur. Le
robot et la communication HTTP/MQTT/backend ne font pas partie de ce frontend.
