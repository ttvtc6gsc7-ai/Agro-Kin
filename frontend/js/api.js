// Client HTTP unique du frontend servi par Django (même origine, pas de CORS).
// Session Django, cookie csrftoken, GET /api/auth/me/.
// Tous les écrans utilisent les données du serveur.

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
  if (window.deconnexionEnCours) return;
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


// Un instantané par actualisation : toutes les vues partagent les mêmes données.
let donneesServeur;
let robotSelectionne = "";
const actualiserDonnees = async () => { donneesServeur = await apiFetch('/supervision/'); };
const zoneServeur = id => donneesServeur.zones.find(z => z.id === id);
const nomZone = id => {
  const zone = zoneServeur(id);
  if (!zone) return 'Zone inconnue';
  const parcelle = donneesServeur.parcelles.find(p => p.id === zone.parcelle);
  return `${parcelle?.nom || 'Parcelle inconnue'} · ${zone.nom}`;
};
const chargerParcelles = async () => donneesServeur.parcelles.map(p => ({
  ...p, id: String(p.id), lieu: p.localisation,
  zones: donneesServeur.zones.filter(z => z.parcelle === p.id).map(z => ({
    ...z, id: String(z.id), parcelle_id: String(z.parcelle), culture_id: String(z.culture),
    culture: donneesServeur.cultures.find(c => c.id === z.culture)?.nom || 'Culture inconnue'
  }))
}));
const chargerMesures = async () => donneesServeur.mesures.map(m => ({
  type: 'mesure_humidite', zone: nomZone(m.zone), zone_id: String(m.zone), robot_id: String(m.robot),
  mission_id: String(m.mission), valeur: m.valeur_brute, horodatage: m.date_heure,
  etat: m.est_valide ? 'valide' : 'invalide', detail: m.motif_invalidation || `Humidité brute : ${m.valeur_brute}`,
  message_id: m.message_id
}));
const chargerMissions = async () => donneesServeur.missions.map(m => ({
  mission_id: String(m.id), robot_id: String(m.robot), horodatage: m.date_debut || m.date_mission,
  debut: m.date_debut, fin: m.date_fin, etat: m.statut,
  zones: m.etapes.map(e => nomZone(e.zone)), resultat: `Transmission : ${m.etat_transmission.replaceAll('_', ' ')}`
}));
const chargerIncidents = async () => donneesServeur.incidents.map(i => ({
  type: ({obstacle: 'obstacle_detecte', communication: 'perte_communication', mesure: 'erreur_mesure'})[i.type_incident] || i.type_incident,
  zone: nomZone(donneesServeur.mesures.find(m => m.id === i.mesure)?.zone),
  robot_id: i.robot == null ? null : String(i.robot), mission_id: i.mission == null ? null : String(i.mission),
  horodatage: i.date_incident, detail: i.description, etat: i.statut
}));
const chargerIrrigations = async () => donneesServeur.irrigations.map(i => ({
  debut: i.date_irrigation, fin: null, zone: nomZone(i.zone), mission_id: String(i.mission || ''),
  duree: i.duree_reelle, volume: i.volume,
  humidite_avant: donneesServeur.mesures.find(m => m.id === i.mesure_source)?.valeur_brute ?? null,
  humidite_apres: null, temperature_avant: null, etat: i.statut
}));
const chargerEtatRobot = async () => {
  const robot = donneesServeur.robots.find(r => String(r.id) === robotSelectionne) || donneesServeur.robots[0];
  robotSelectionne = robot ? String(robot.id) : '';
  const missions = donneesServeur.missions.filter(m => m.robot === robot?.id);
  return {
    id: robotSelectionne, robot_id: robot?.identifiant, nom: robot?.nom,
    etat: robot?.etat_connexion || 'inconnu', derniere_communication: robot?.derniere_connexion,
    probleme: robot ? (missions.some(m => m.statut === 'interrompue') ? 'Une mission est interrompue' : '') : 'Aucun robot enregistré'
  };
};
const chargerHistorique = async () => {
  const [mesures, incidents] = await Promise.all([chargerMesures(), chargerIncidents()]);
  const missions = donneesServeur.missions.flatMap(m => [
    ...(m.date_debut ? [{type: 'demarrage_mission', horodatage: m.date_debut}] : []),
    ...(m.date_fin ? [{type: 'fin_mission', horodatage: m.date_fin}] : [])
  ].map(e => ({...e, mission_id: String(m.id), robot_id: String(m.robot), etat: m.statut})));
  const etapes = donneesServeur.missions.flatMap(m => m.etapes.filter(e => e.date_debut).map(e => ({
    type: 'arrivee_zone', horodatage: e.date_debut, zone: nomZone(e.zone), mission_id: String(m.id), robot_id: String(m.robot), etat: e.statut
  })));
  const irrigations = donneesServeur.irrigations.map(i => ({
    type: 'operation_irrigation', horodatage: i.date_irrigation, zone: nomZone(i.zone),
    mission_id: String(i.mission || ''), detail: `Irrigation : ${i.statut.replaceAll('_', ' ')}`, etat: i.statut
  }));
  return [...mesures, ...incidents, ...missions, ...etapes, ...irrigations];
};
const enregistrerParcelle = p => envoyerJSON(p.id ? `/parcelles/${Number(p.id)}/` : '/parcelles/', p.id ? 'PUT' : 'POST', {
  nom: p.nom, localisation: p.lieu, superficie: p.superficie
});
const enregistrerZone = z => envoyerJSON(z.id ? `/zones/${Number(z.id)}/` : '/zones/', z.id ? 'PUT' : 'POST', {
  nom: z.nom, parcelle: Number(z.parcelle_id), culture: Number(z.culture)
});
const enregistrerCulture = c => envoyerJSON('/cultures/', 'POST', c);
const enregistrerMission = async m => {
  const result = await envoyerJSON('/missions/', 'POST', {
    robot: Number(m.robot), date_mission: m.horodatage, zones: m.zones.map(Number)
  });
  return {...result, mission_id: result.id};
};
