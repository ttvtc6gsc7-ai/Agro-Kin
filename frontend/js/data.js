// Données de démonstration uniquement : aucun message ne provient du robot.
// Les objets suivent le format des messages reçus et peuvent être remplacés par l'API.
const DONNEES_DEMO = true;

// Format reçu du robot : robot_id, mission_id, type, zone, valeur, unite,
// horodatage, etat et message_id. Les champs supplémentaires décrivent certains
// événements. Toutes les valeurs ci-dessous sont simulées.
const messagesRobot = [
  { robot_id: "RAK-01", mission_id: "M-001", type: "demarrage_mission", zone: "Zone 1", valeur: null, unite: null, horodatage: "2026-11-07T08:00:00-06:00", etat: "en_cours", message_id: "msg-001", detail: "Début de mission", resultat: null },
  { robot_id: "RAK-01", mission_id: "M-001", type: "arrivee_zone", zone: "Zone 1", valeur: null, unite: null, horodatage: "2026-11-07T08:03:00-06:00", etat: "en_cours", message_id: "msg-002", detail: "Arrivée en zone" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "mesure_humidite", zone: "Zone 1", valeur: 52, unite: "valeur brute", horodatage: "2026-11-07T08:04:00-06:00", etat: "valide", message_id: "msg-003" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "mesure_temperature", zone: "Zone 1", valeur: 24.1, unite: "°C", horodatage: "2026-11-07T08:04:10-06:00", etat: "valide", message_id: "msg-004" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "debut_arrosage", zone: "Zone 1", valeur: null, unite: null, horodatage: "2026-11-07T08:05:00-06:00", etat: "en_cours", message_id: "msg-005", volume: 4.2, humidite_avant: 52, temperature_avant: 24.1, motif: "Humidité insuffisante" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "fin_arrosage", zone: "Zone 1", valeur: 4.2, unite: "L", horodatage: "2026-11-07T08:06:30-06:00", etat: "termine", message_id: "msg-006", volume: 4.2, duree: 90, humidite_avant: 52, humidite_apres: 61, temperature_avant: 24.1, motif: "Humidité insuffisante" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "deplacement", zone: "Zone 2", valeur: null, unite: null, horodatage: "2026-11-07T08:08:00-06:00", etat: "avance", message_id: "msg-007", detail: "Avance" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "arrivee_zone", zone: "Zone 2", valeur: null, unite: null, horodatage: "2026-11-07T08:10:00-06:00", etat: "en_cours", message_id: "msg-008", detail: "Arrivée en zone" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "mesure_humidite", zone: "Zone 2", valeur: 38, unite: "valeur brute", horodatage: "2026-11-07T08:11:00-06:00", etat: "valide", message_id: "msg-009" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "mesure_temperature", zone: "Zone 2", valeur: 25.3, unite: "°C", horodatage: "2026-11-07T08:11:10-06:00", etat: "valide", message_id: "msg-010" },
  { robot_id: "RAK-01", mission_id: "M-001", type: "fin_mission", zone: "Zone 2", valeur: null, unite: null, horodatage: "2026-11-07T08:20:00-06:00", etat: "terminee", message_id: "msg-011", resultat: "2 zones visitées" },
  { robot_id: "RAK-01", mission_id: "M-002", type: "demarrage_mission", zone: "Zone 1", valeur: null, unite: null, horodatage: "2026-11-08T14:00:00-06:00", etat: "en_cours", message_id: "msg-012", detail: "Début de mission", resultat: null },
  { robot_id: "RAK-01", mission_id: "M-002", type: "mesure_humidite", zone: "Zone 2", valeur: 33, unite: "valeur brute", horodatage: "2026-11-08T14:05:00-06:00", etat: "valide", message_id: "msg-013" },
  { robot_id: "RAK-01", mission_id: "M-002", type: "mesure_temperature", zone: "Zone 2", valeur: 26.2, unite: "°C", horodatage: "2026-11-08T14:05:10-06:00", etat: "valide", message_id: "msg-014" },
  { robot_id: "RAK-01", mission_id: "M-002", type: "debut_arrosage", zone: "Zone 2", valeur: null, unite: null, horodatage: "2026-11-08T14:06:00-06:00", etat: "en_cours", message_id: "msg-015", volume: 3.8, humidite_avant: 33, temperature_avant: 26.2, motif: "Humidité insuffisante" },
  { robot_id: "RAK-01", mission_id: "M-002", type: "fin_arrosage", zone: "Zone 2", valeur: 3.8, unite: "L", horodatage: "2026-11-08T14:07:30-06:00", etat: "termine", message_id: "msg-016", volume: 3.8, duree: 90, humidite_avant: 33, humidite_apres: 45, temperature_avant: 26.2, motif: "Humidité insuffisante" },
  { robot_id: "RAK-01", mission_id: "M-002", type: "obstacle_detecte", zone: "Zone 2", valeur: null, unite: null, horodatage: "2026-11-08T14:08:00-06:00", etat: "arrete", message_id: "msg-017", detail: "Obstacle devant la zone" },
  { robot_id: "RAK-01", mission_id: "M-002", type: "fin_mission", zone: "Zone 2", valeur: null, unite: null, horodatage: "2026-11-08T14:08:30-06:00", etat: "interrompue", message_id: "msg-018", resultat: "Mission interrompue : obstacle détecté" },
  { robot_id: "RAK-01", mission_id: "M-003", type: "demarrage_mission", zone: "Zone 3", valeur: null, unite: null, horodatage: "2026-11-08T16:30:00-06:00", etat: "en_cours", message_id: "msg-019", detail: "Début de mission" },
  { robot_id: "RAK-01", mission_id: "M-003", type: "mesure_humidite", zone: "Zone 3", valeur: null, unite: "valeur brute", horodatage: "2026-11-08T16:35:00-06:00", etat: "invalide", message_id: "msg-020", detail: "Capteur sans valeur" },
  { robot_id: "RAK-01", mission_id: "M-003", type: "erreur_mesure", zone: "Zone 3", valeur: null, unite: null, horodatage: "2026-11-08T16:35:05-06:00", etat: "invalide", message_id: "msg-021", detail: "Arrosage interdit : mesure invalide" },
  { robot_id: "RAK-01", mission_id: "M-003", type: "perte_communication", zone: "Zone 3", valeur: null, unite: null, horodatage: "2026-11-08T16:40:00-06:00", etat: "deconnecte", message_id: "msg-022", detail: "Dernière communication reçue" }
];

// Référentiel de démonstration; les modifications de gestion sont stockées localement.
const donneesParcelles = [{
  id: "P-001",
  nom: "Parcelle expérimentale A",
  lieu: "UCC, Kinshasa",
  zones: [
    { id: "Z-001", parcelle_id: "P-001", nom: "Zone 1", culture: "Amarante" },
    { id: "Z-002", parcelle_id: "P-001", nom: "Zone 2", culture: "Tomate" },
    { id: "Z-003", parcelle_id: "P-001", nom: "Zone 3", culture: "Chou" }
  ]
}];

// Missions reçues simulées; les nouvelles missions restent planifiées en démo.
const donneesMissions = [
  { mission_id: "M-001", horodatage: "2026-11-07T08:00:00-06:00", fin: "2026-11-07T08:20:00-06:00", zones: ["Zone 1", "Zone 2"], etat: "terminee", resultat: "2 zones visitées" },
  { mission_id: "M-002", horodatage: "2026-11-08T14:00:00-06:00", fin: "2026-11-08T14:08:30-06:00", zones: ["Zone 1", "Zone 2"], etat: "interrompue", resultat: "Mission interrompue : obstacle détecté" },
  { mission_id: "M-003", horodatage: "2026-11-08T16:30:00-06:00", fin: null, zones: ["Zone 3"], etat: "en_cours", resultat: "Mesure invalide; communication perdue" }
];

// Dernier état connu dans le jeu de données de démonstration.
const donneesEtatRobot = {
  robot_id: "RAK-01",
  etat: "deconnecte",
  derniere_communication: "2026-11-08T16:40:00-06:00",
  probleme: "Perte de communication"
};
