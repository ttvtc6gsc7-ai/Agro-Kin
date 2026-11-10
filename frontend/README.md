# RoboAgri-Kin – Frontend

Frontend du projet universitaire RoboAgri-Kin, réalisé en HTML5, CSS3,
JavaScript, Bootstrap 5 et Plotly. Ouvrir `index.html` (connexion Internet
requise pour les bibliothèques chargées depuis les CDN).

L'interface permet de gérer les parcelles et les zones, de préparer des missions,
et de configurer les seuils et limites d'irrigation. Elle n'envoie aucune
commande manuelle au robot. Les mesures et états du robot restent en lecture
seule. En mode démonstration, les écritures de gestion sont stockées dans
`localStorage` et ne sont pas transmises au robot ni à un serveur.

- `css/style.css` : charte visuelle et mise en page responsive.
- `js/data.js` : données de démonstration explicitement signalées dans l'interface.
- `js/api.js` : accès unique aux données de démonstration et stockage local des
  opérations de gestion, à remplacer par des appels au backend.
- `js/app.js` : navigation, affichage des pages, tableaux, graphiques et états;
  actualisation périodique toutes les 10 secondes.
- Pages : tableau de bord, parcelles et zones, surveillance du robot, mesures,
  missions, irrigation, incidents, historique et rapports.

Les valeurs d'humidité sont présentées comme des valeurs brutes. Les seuils
doivent être déterminés par étalonnage et essais. Le robot et la communication
HTTP/MQTT/backend ne font pas partie de ce frontend.
