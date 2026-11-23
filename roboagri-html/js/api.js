// Couche d'accès unique utilisée par app.js.
// Dans cette version, les données du robot sont simulées et les écritures sont locales;
// remplacer ces fonctions par des échanges backend ne crée pas, à lui seul, un lien avec le robot.
const CLE_LOCAL = {
  parcelles: "roboagri.parcelles",
  zones: "roboagri.zones",
  missions: "roboagri.missions"
};

const lireLocal = (cle, valeursInitiales) => {
  const contenu = localStorage.getItem(cle);
  if (contenu === null) return structuredClone(valeursInitiales);
  const valeurs = JSON.parse(contenu);
  if (!Array.isArray(valeurs)) throw new Error(`Données locales invalides : ${cle}`);
  return valeurs;
};

// Les données modifiables restent dans le navigateur, sous forme de tableaux JSON.
const enregistrerLocal = (cle, valeurs) => localStorage.setItem(cle, JSON.stringify(valeurs));
const nouvelIdentifiant = prefixe => `${prefixe}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

// Ces chargeurs exposent les données de démonstration dans les formats attendus par app.js.
// GET /api/historique/ -> [{robot_id, mission_id, type, zone, valeur, unite,
// horodatage, etat, message_id, ...}]. Les événements sont en lecture seule.
const chargerHistorique = async () => messagesRobot.slice();

// GET /api/mesures/ -> mêmes champs de message, avec type mesure_humidite
// ou mesure_temperature; une valeur absente reste null et n'est pas corrigée.
const chargerMesures = async () => messagesRobot
  .filter(message => ["mesure_humidite", "mesure_temperature"].includes(message.type))
  .slice();

// GET /api/irrigations/ -> [{debut, fin, zone, mission_id, duree, volume,
// humidite_avant, humidite_apres, temperature_avant, decision, etat}].
const chargerIrrigations = async () => {
  const debuts = messagesRobot.filter(message => message.type === "debut_arrosage");
  const fins = messagesRobot.filter(message => message.type === "fin_arrosage");
  const irrigations = debuts.map(debut => {
    const fin = fins.find(message => message.mission_id === debut.mission_id &&
      message.zone === debut.zone && message.horodatage >= debut.horodatage);
    return {
      debut: debut.horodatage,
      fin: fin?.horodatage || null,
      zone: debut.zone,
      mission_id: debut.mission_id,
      duree: fin?.duree ?? null,
      volume: fin?.volume ?? debut.volume ?? null,
      humidite_avant: debut.humidite_avant ?? null,
      humidite_apres: fin?.humidite_apres ?? null,
      temperature_avant: debut.temperature_avant ?? null,
      decision: "effectue",
      motif: debut.motif || "Arrosage rapporté par le robot",
      etat: fin ? "terminee" : "en_cours"
    };
  });
  const refus = messagesRobot.filter(message => message.type === "erreur_mesure").map(message => ({
    debut: message.horodatage,
    fin: null,
    zone: message.zone,
    mission_id: message.mission_id,
    duree: null,
    volume: null,
    humidite_avant: null,
    humidite_apres: null,
    temperature_avant: null,
    decision: "interdit",
    motif: "Arrosage interdit : mesure invalide",
    etat: "interdit"
  }));
  return [...irrigations, ...refus].sort((a, b) => b.debut.localeCompare(a.debut));
};

// GET /api/missions/ -> [{mission_id, horodatage, fin, zones: string[],
// etat: planifiee|en_cours|terminee|interrompue, resultat}].
const chargerMissions = async () => [
  ...donneesMissions.map(mission => ({ ...mission, zones: [...mission.zones] })),
  ...lireLocal(CLE_LOCAL.missions, [])
];

// GET /api/incidents/ -> messages robot de type obstacle, communication ou mesure.
const chargerIncidents = async () => messagesRobot
  .filter(message => ["obstacle_detecte", "perte_communication", "erreur_mesure"].includes(message.type))
  .slice();

// GET /api/robot/etat/ -> {robot_id, etat, derniere_communication, probleme}.
const chargerEtatRobot = async () => ({ ...donneesEtatRobot });

// GET /api/parcelles/ -> [{id, nom, lieu, zones: [{id, parcelle_id, nom, culture}]}].
const chargerParcelles = async () => {
  const parcellesDemo = donneesParcelles.map(({ id, nom, lieu }) => ({ id, nom, lieu }));
  const parcelles = lireLocal(CLE_LOCAL.parcelles, parcellesDemo);
  const zonesDemo = donneesParcelles.flatMap(parcelle => parcelle.zones);
  const zones = lireLocal(CLE_LOCAL.zones, zonesDemo);
  return parcelles.map(parcelle => ({
    ...parcelle,
    zones: zones.filter(zone => zone.parcelle_id === parcelle.id)
  }));
};

// POST/PUT /api/parcelles/ {id?, nom, lieu}; renvoie {id, nom, lieu}.
const enregistrerParcelle = async parcelle => {
  const parcelles = lireLocal(CLE_LOCAL.parcelles, donneesParcelles.map(({ id, nom, lieu }) => ({ id, nom, lieu })));
  const valeur = { ...parcelle, id: parcelle.id || nouvelIdentifiant("P") };
  const index = parcelles.findIndex(item => item.id === valeur.id);
  if (index < 0) parcelles.push(valeur);
  else parcelles[index] = valeur;
  enregistrerLocal(CLE_LOCAL.parcelles, parcelles);
  return valeur;
};

// POST/PUT /api/zones/ {id?, parcelle_id, nom, culture}; renvoie la zone enregistrée.
const enregistrerZone = async zone => {
  const zonesDemo = donneesParcelles.flatMap(parcelle => parcelle.zones);
  const zones = lireLocal(CLE_LOCAL.zones, zonesDemo);
  const valeur = { ...zone, id: zone.id || nouvelIdentifiant("Z") };
  const index = zones.findIndex(item => item.id === valeur.id);
  if (index < 0) zones.push(valeur);
  else zones[index] = valeur;
  enregistrerLocal(CLE_LOCAL.zones, zones);
  return valeur;
};

// Enregistre seulement une mission planifiée dans localStorage.
// Cette fonction n'envoie ni mission au serveur ni commande à un robot.
const enregistrerMission = async mission => {
  const missions = lireLocal(CLE_LOCAL.missions, []);
  const valeur = {
    ...mission,
    mission_id: mission.mission_id || nouvelIdentifiant("M"),
    zones: [...mission.zones],
    fin: null,
    etat: "planifiee",
    resultat: "Mission planifiée (démonstration locale)"
  };
  missions.push(valeur);
  enregistrerLocal(CLE_LOCAL.missions, missions);
  return valeur;
};
