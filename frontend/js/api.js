// Client HTTP unique du frontend servi par Django (même origine, pas de CORS).
// Session Django, cookie csrftoken, GET /api/auth/me/.
// Parcelles, zones et cultures passent par l'API réelle ; les autres modules restent en démonstration.

const API_BASE = "/api";

class ErreurAPI extends Error {
  constructor(message, { statut = 0, code = null, details = null } = {}) {
    super(message);
    this.name = "ErreurAPI";
    this.statut = statut;
    this.code = code;
    this.details = details;
  }
}

const lireCookie = nom => {
  const prefixe = `${nom}=`;
  const morceau = document.cookie.split(";").map(part => part.trim()).find(part => part.startsWith(prefixe));
  return morceau ? decodeURIComponent(morceau.slice(prefixe.length)) : "";
};

const jetonCSRF = () => lireCookie("csrftoken");

const messageErreurHTTP = async response => {
  const fallback = `Erreur HTTP ${response.status}.`;
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") return payload.detail;
    if (Array.isArray(payload?.detail)) return payload.detail.map(item => item.string || item).join(" ");
    if (payload && typeof payload === "object") {
      return Object.entries(payload).map(([cle, valeur]) =>
        `${cle} : ${Array.isArray(valeur) ? valeur.join(" ") : valeur}`
      ).join(" ");
    }
  } catch (_erreur) {
    /* Réponse non JSON : message générique. */
  }
  return fallback;
};

const redirigerVersConnexion = () => {
  if (typeof window === "undefined" || !window.location) return;
  if (window.location.pathname.startsWith("/connexion")) return;
  const suivant = `${window.location.pathname}${window.location.search}`;
  window.location.assign(`/connexion/?next=${encodeURIComponent(suivant)}`);
};

// Analyse robuste distinguant non-authentifié, session expirée, permission refusée, CSRF et 500.
const analyserReponseErreur = (statut, detail, chemin = "") => {
  const texte = String(detail || "").toLowerCase();
  const estAuthMe = chemin.includes("/auth/me/");
  const estCsrf = texte.includes("csrf");

  // Cas 4 : Erreur CSRF -> ne pas détruire la session, ne pas rediriger
  if (estCsrf) {
    return {
      code: "CSRF_ERROR",
      message: "Erreur de sécurité CSRF (jeton manquant ou invalide). Veuillez recharger la page.",
      doitRediriger: false
    };
  }

  // Cas 1 : Utilisateur non authentifié (/auth/me/ renvoie 401 ou 403)
  if (estAuthMe && (statut === 401 || statut === 403)) {
    return {
      code: "NON_AUTHENTIFIE",
      message: "Session absente ou invalide. Redirection vers la page de connexion.",
      doitRediriger: true
    };
  }

  // Cas 2 : Statut 401 explicite sur n'importe quel endpoint -> perte de session
  if (statut === 401) {
    return {
      code: "SESSION_EXPIREE",
      message: "Votre session a expiré. Redirection vers la page de connexion.",
      doitRediriger: true
    };
  }

  // Traitement du statut 403 Forbidden sur les autres endpoints
  if (statut === 403) {
    const estSansAuth = texte.includes("credentials") ||
      texte.includes("informations d'authentification") ||
      texte.includes("identifiants d'authentification") ||
      texte.includes("authentification non fournies") ||
      texte.includes("not_authenticated");

    if (estSansAuth) {
      return {
        code: "SESSION_EXPIREE",
        message: "Votre session a expiré. Redirection vers la page de connexion.",
        doitRediriger: true
      };
    }

    // Cas 3 : Erreur de permission 403 (utilisateur authentifié mais droits insuffisants)
    return {
      code: "PERMISSION_REFUSEE",
      message: detail || "Accès refusé : vous n'avez pas les autorisations nécessaires pour cette action.",
      doitRediriger: false
    };
  }

  // Cas 5 : Erreur interne serveur (>= 500)
  if (statut >= 500) {
    return {
      code: "ERREUR_SERVEUR",
      message: `Erreur interne du serveur (${statut}). Veuillez réessayer ultérieurement.`,
      doitRediriger: false
    };
  }

  return {
    code: "ERREUR_HTTP",
    message: detail || `Erreur HTTP ${statut}.`,
    doitRediriger: false
  };
};

const apiFetch = async (chemin, options = {}) => {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  if (method !== "GET" && method !== "HEAD") {
    const csrf = jetonCSRF();
    if (!csrf) {
      throw new ErreurAPI(
        "Jeton CSRF introuvable. Ouvrez l'application via Django (pas en fichier local) et rechargez la page.",
        { statut: 403, code: "CSRF_ERROR" }
      );
    }
    headers.set("X-CSRFToken", csrf);
    if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
  }
  let response;
  try {
    response = await fetch(`${API_BASE}${chemin.startsWith("/") ? chemin : `/${chemin}`}`, {
      ...options,
      method,
      headers,
      credentials: "same-origin"
    });
  } catch (_erreur) {
    throw new ErreurAPI(
      "Le serveur RoboAgri-Kin est injoignable. Vérifiez que Django est démarré sur le réseau local.",
      { statut: 0, code: "RESEAU_INJOIGNABLE" }
    );
  }
  if (response.status === 204) return null;
  if (!response.ok) {
    const detail = await messageErreurHTTP(response);
    const analyse = analyserReponseErreur(response.status, detail, chemin);
    if (analyse.doitRediriger) {
      redirigerVersConnexion();
    }
    throw new ErreurAPI(analyse.message, {
      statut: response.status,
      code: analyse.code,
      details: detail
    });
  }
  if (response.status === 201 || response.headers.get("Content-Type")?.includes("application/json")) {
    return response.json();
  }
  return response;
};

const verifierSession = async () => {
  try {
    return await apiFetch("/auth/me/");
  } catch (erreur) {
    if (erreur instanceof ErreurAPI && (erreur.statut === 401 || erreur.statut === 403 || erreur.code === "NON_AUTHENTIFIE" || erreur.code === "SESSION_EXPIREE")) {
      return null;
    }
    throw erreur;
  }
};

const extraireListe = donnees => {
  if (Array.isArray(donnees)) return donnees;
  if (Array.isArray(donnees?.results)) return donnees.results;
  return [];
};

const envoyerJSON = (chemin, method, corps) => apiFetch(chemin, {
  method,
  body: JSON.stringify(corps)
});

const CLE_LOCAL = {
  missions: "roboagri.missions",
  configurations: "roboagri.configurations-irrigation"
};

const lireLocal = (cle, valeursInitiales) => {
  const contenu = localStorage.getItem(cle);
  if (contenu === null) return structuredClone(valeursInitiales);
  const valeurs = JSON.parse(contenu);
  if (!Array.isArray(valeurs)) throw new Error(`Données locales invalides : ${cle}`);
  return valeurs;
};

const enregistrerLocal = (cle, valeurs) => localStorage.setItem(cle, JSON.stringify(valeurs));
const nouvelIdentifiant = prefixe => `${prefixe}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

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

// GET /api/cultures/ -> [{id, nom, description, type_culture}].
const chargerCultures = async () => extraireListe(await apiFetch("/cultures/"));

// GET /api/zones/ -> [{id, nom, parcelle, culture}] (clés étrangères numériques).
const chargerZones = async () => extraireListe(await apiFetch("/zones/"));

// GET /api/parcelles/ composé côté client : chaque parcelle reçoit ses zones
// (filtre zone.parcelle) et le nom de culture résolu via /api/cultures/.
const chargerParcelles = async () => {
  const [parcelles, zones, cultures] = await Promise.all([
    apiFetch("/parcelles/"),
    chargerZones(),
    chargerCultures()
  ]);
  chargerParcelles.dernieresCultures = cultures;
  const parCulture = new Map(cultures.map(culture => [Number(culture.id), culture]));
  return extraireListe(parcelles).map(parcelle => ({
    ...parcelle,
    zones: zones.filter(zone => Number(zone.parcelle) === Number(parcelle.id)).map(zone => ({
      ...zone,
      cultureNom: parCulture.get(Number(zone.culture))?.nom || "Culture inconnue"
    }))
  }));
};

// POST /api/parcelles/ ou PUT /api/parcelles/{id}/ {nom, superficie, localisation}.
const enregistrerParcelle = async parcelle => {
  const corps = {
    nom: parcelle.nom,
    superficie: parcelle.superficie,
    localisation: parcelle.localisation
  };
  if (parcelle.id != null && parcelle.id !== "") {
    return envoyerJSON(`/parcelles/${Number(parcelle.id)}/`, "PUT", corps);
  }
  return envoyerJSON("/parcelles/", "POST", corps);
};

// POST /api/zones/ ou PUT /api/zones/{id}/ {nom, parcelle, culture} (ids numériques).
const enregistrerZone = async zone => {
  const corps = {
    nom: zone.nom,
    parcelle: Number(zone.parcelle),
    culture: Number(zone.culture)
  };
  if (zone.id != null && zone.id !== "") {
    return envoyerJSON(`/zones/${Number(zone.id)}/`, "PUT", corps);
  }
  return envoyerJSON("/zones/", "POST", corps);
};

// POST /api/cultures/ ou PUT /api/cultures/{id}/ {nom, type_culture, description}.
const enregistrerCulture = async culture => {
  const corps = {
    nom: culture.nom,
    type_culture: culture.type_culture,
    description: culture.description || ""
  };
  if (culture.id != null && culture.id !== "") {
    return envoyerJSON(`/cultures/${Number(culture.id)}/`, "PUT", corps);
  }
  return envoyerJSON("/cultures/", "POST", corps);
};

// POST /api/missions/ {horodatage, zones: string[]}; état initial planifiee.
// Le backend recevra cette préparation; aucun ordre manuel au robot n'est émis ici.
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

// GET /api/configurations-irrigation/ -> [{zone, seuil_humidite,
// duree_max_secondes, volume_max_litres?}].
const chargerConfigurationsIrrigation = async () =>
  lireLocal(CLE_LOCAL.configurations, []);

// POST/PUT /api/configurations-irrigation/ {zone, seuil_humidite,
// duree_max_secondes, volume_max_litres?}; renvoie la configuration enregistrée.
const enregistrerConfigurationIrrigation = async configuration => {
  const configurations = lireLocal(CLE_LOCAL.configurations, []);
  const valeur = { ...configuration };
  const index = configurations.findIndex(item => item.zone === valeur.zone);
  if (index < 0) configurations.push(valeur);
  else configurations[index] = valeur;
  enregistrerLocal(CLE_LOCAL.configurations, configurations);
  return valeur;
};
