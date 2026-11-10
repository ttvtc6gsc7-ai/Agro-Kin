// Navigation, formulaires de gestion et affichage des données reçues.
const MENU = [
  ["index", "grid", "Tableau de bord"],
  ["parcelles", "map", "Parcelles et zones"],
  ["robot", "robot", "Surveillance du robot"],
  ["mesures", "droplet", "Mesures"],
  ["missions", "flag", "Missions"],
  ["irrigation", "moisture", "Irrigation"],
  ["incidents", "exclamation-triangle", "Incidents"],
  ["historique", "clock-history", "Historique"],
  ["rapports", "bar-chart", "Rapports et statistiques"]
];
const page = document.body.dataset.page;
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g, character => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[character]);
const vide = message => `<div class="vide">${escapeHTML(message)}</div>`;
const ETAT_ROBOT = {
  connecte: ["ok", "Connecté"], deconnecte: ["off", "Déconnecté"],
  en_mission: ["cours", "En mission"], arrete: ["err", "Arrêté"]
};
const ETAT_MISSION = {
  planifiee: ["off", "Planifiée"], en_cours: ["cours", "En cours"],
  terminee: ["ok", "Terminée"], interrompue: ["err", "Interrompue"]
};
const TYPES = {
  demarrage_mission: "Démarrage de mission", deplacement: "Déplacement",
  arrivee_zone: "Arrivée à une zone", mesure_humidite: "Mesure d'humidité",
  mesure_temperature: "Mesure de température", obstacle_detecte: "Obstacle détecté et arrêt",
  debut_arrosage: "Début d'arrosage", fin_arrosage: "Fin d'arrosage",
  perte_communication: "Perte de communication", erreur_mesure: "Erreur de mesure",
  fin_mission: "Fin de mission"
};
const TYPE_CLASSES = {
  demarrage_mission: "cours", deplacement: "off", arrivee_zone: "ok",
  mesure_humidite: "cours", mesure_temperature: "cours", obstacle_detecte: "err",
  debut_arrosage: "ok", fin_arrosage: "ok", perte_communication: "err",
  erreur_mesure: "err", fin_mission: "off"
};
const badge = status => {
  const [className, label] = status || ["off", "Inconnu"];
  return `<span class="etat etat-${className}">${escapeHTML(label)}</span>`;
};
const badgeEtatRobot = state => badge(ETAT_ROBOT[state] || ["off", "Inconnu"]);
const badgeEtatMission = state => badge(ETAT_MISSION[state] || ["off", "Inconnu"]);
const badgeType = type => badge([TYPE_CLASSES[type] || "off", TYPES[type] || type || "Inconnu"]);
const dateHeure = value => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? escapeHTML(value) :
    new Intl.DateTimeFormat("fr-FR", { dateStyle: "short", timeStyle: "medium" }).format(date);
};
const numeric = value => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));
const valeurBrute = value => numeric(value) ? `${escapeHTML(value)} <small class="text-muted">valeur brute</small>` : "—";
const table = (heads, rows, message) => rows.length
  ? `<div class="table-responsive"><table class="table align-middle"><thead><tr>${heads.map(head => `<th scope="col">${escapeHTML(head)}</th>`).join("")}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${cell ?? "—"}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`
  : vide(message);
const renderTable = (id, headers, rows, message) => {
  const element = $(id);
  if (element) element.innerHTML = table(headers, rows, message);
};
const renderChart = (id, traces, layout, message) => {
  const element = $(id);
  if (!element) return;
  if (!traces.some(trace => trace.x.length)) {
    if (window.Plotly) Plotly.purge(element);
    element.innerHTML = vide(message);
    return;
  }
  Plotly.react(element, traces, {
    margin: { t: 12, r: 12, b: 48, l: 54 },
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: "#4b5563" }, ...layout
  }, { responsive: true, displayModeBar: false });
};
const showLoadError = error => {
  console.error("Impossible de charger les données.", error);
  let alert = $("loadError");
  if (!alert) {
    alert = document.createElement("div");
    alert.id = "loadError";
    alert.className = "alert alert-danger";
    alert.setAttribute("role", "alert");
    $("appFooter")?.before(alert);
  }
  let detail = "Les données n'ont pas pu être actualisées.";
  if (error instanceof ErreurAPI) {
    if (error.code === "PERMISSION_REFUSEE") {
      detail = error.message || "Accès restreint : votre compte ne dispose pas des droits requis.";
    } else if (error.code === "CSRF_ERROR") {
      detail = error.message;
    } else if (error.code === "ERREUR_SERVEUR") {
      detail = error.message;
    } else if (error.message) {
      detail = error.message;
    }
  }
  alert.textContent = `${detail} Une nouvelle tentative aura lieu dans 10 secondes.`;
};
const showFormMessage = (form, message, success = false) => {
  let alert = form.querySelector(".form-feedback");
  if (!alert) {
    alert = document.createElement("div");
    alert.className = "col-12 form-feedback alert mb-0";
    alert.setAttribute("role", "status");
    form.append(alert);
  }
  alert.className = `form-feedback alert mb-0 ${success ? "alert-success" : "alert-danger"}`;
  alert.textContent = message;
};
const resetFormFeedback = form => form.querySelector(".form-feedback")?.remove();

document.body.insertAdjacentHTML("afterbegin", `<nav class="sidebar" id="sidebar" aria-label="Navigation principale">
  <div class="brand"><i class="bi bi-flower2" aria-hidden="true"></i> Robo<span>Agri</span>-Kin</div>
  ${MENU.map(([key, icon, label]) => `<a href="${key}.html" class="${key === page ? "active" : ""}"${key === page ? ' aria-current="page"' : ""}><i class="bi bi-${icon}" aria-hidden="true"></i> ${label}</a>`).join("")}
  <p class="sidebar-note">Les formulaires gèrent les données. Le robot exécute seul ses missions ; aucune commande manuelle n'est disponible ici.</p>
  <div class="sidebar-session">
    <p class="small mb-2" id="sessionUser">Session : vérification…</p>
    <button class="btn btn-sm btn-outline-light w-100" id="logoutButton" type="button">Déconnexion</button>
  </div>
</nav>`);
const main = document.querySelector("main");
main.insertAdjacentHTML("afterbegin", `<div class="topbar-mobile"><button class="btn btn-outline-secondary" id="menuToggle" type="button" aria-controls="sidebar" aria-expanded="false" aria-label="Ouvrir le menu"><i class="bi bi-list" aria-hidden="true"></i></button><strong>RoboAgri-Kin</strong></div>`);
document.body.insertAdjacentHTML("beforeend", `<footer class="app-footer" id="appFooter"><span>Les mesures et états du robot sont affichés en lecture seule.</span><span id="lastUpdate">Dernière mise à jour : en attente</span></footer>`);
$("menuToggle")?.addEventListener("click", event => {
  const expanded = $("sidebar").classList.toggle("open");
  event.currentTarget.setAttribute("aria-expanded", String(expanded));
});
if (DONNEES_DEMO) {
  main.querySelector("h1")?.insertAdjacentHTML("afterend", `<div class="badge-demo" role="note"><i class="bi bi-info-circle" aria-hidden="true"></i> <strong>Données de démonstration</strong> : les données reçues sont simulées ; les formulaires sont enregistrés localement.</div>`);
}

let dernierHistorique = [];
let derniereZoneOptions = "";
const memeIdentifiant = (a, b) => a != null && b != null && String(a) === String(b);
const updateZoneCache = (parcels, cultures = window.culturesCourantes || []) => {
  window.parcellesCourantes = parcels;
  window.culturesCourantes = cultures;
  window.zonesCourantes = parcels.flatMap(parcel =>
    parcel.zones.map(zone => ({ ...zone, parcelleNom: parcel.nom })));
};
const messageErreurFormulaire = (error, fallback) => {
  if (error instanceof ErreurAPI) {
    if (error.code === "CSRF_ERROR") {
      return "Erreur de sécurité CSRF (jeton manquant ou invalide). Veuillez actualiser la page.";
    }
    if (error.code === "PERMISSION_REFUSEE") {
      return "Action refusée : votre profil ne dispose pas des droits de modification.";
    }
    if (error.message) return error.message;
  }
  return fallback;
};
const findZone = (parcelles, zoneId) => parcelles.flatMap(parcelle =>
  parcelle.zones.map(zone => ({ ...zone, parcelleNom: parcelle.nom }))
).find(zone => memeIdentifiant(zone.id, zoneId));
const labelZone = zone => zone ? `${zone.parcelleNom} · ${zone.nom}` : "Zone inconnue";
const isValidMeasure = record => record.etat === "valide" && numeric(record.valeur) &&
  (record.type !== "mesure_humidite" || Number(record.valeur) >= 0);

const renderHistory = records => {
  const typeFilter = $("historyType")?.value || "";
  const zoneFilter = $("historyZone")?.value || "";
  const dateFilter = $("historyDate")?.value || "";
  const filtered = records.filter(record =>
    (!typeFilter || record.type === typeFilter) &&
    (!zoneFilter || record.zone === zoneFilter) &&
    (!dateFilter || record.horodatage?.slice(0, 10) === dateFilter)
  ).sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage));
  renderTable("historyTable", ["Date et heure", "Type d'événement", "Zone", "Mission", "Détail", "Résultat"],
    filtered.map(record => [
      dateHeure(record.horodatage), badgeType(record.type), escapeHTML(record.zone || "—"),
      escapeHTML(record.mission_id || "—"), escapeHTML(record.detail || record.etat || "—"),
      escapeHTML(record.resultat || "—")
    ]), "Aucun historique reçu.");
};
["historyType", "historyZone", "historyDate"].forEach(id =>
  $(id)?.addEventListener("change", () => renderHistory(dernierHistorique)));

const renderParcelForms = parcels => {
  const select = $("zoneParcel");
  if (!select) return;
  const selected = select.value;
  select.innerHTML = `<option value="">Choisir une parcelle</option>${parcels.map(parcel =>
    `<option value="${escapeHTML(parcel.id)}">${escapeHTML(parcel.nom)}</option>`).join("")}`;
  if (parcels.some(parcel => memeIdentifiant(parcel.id, selected))) select.value = selected;
};
const renderCultureSelect = cultures => {
  const select = $("zoneCulture");
  if (!select) return;
  const selected = select.value;
  select.innerHTML = `<option value="">Choisir une culture</option>${cultures.map(culture =>
    `<option value="${escapeHTML(culture.id)}">${escapeHTML(culture.nom)}</option>`).join("")}`;
  if (cultures.some(culture => memeIdentifiant(culture.id, selected))) select.value = selected;
};
const renderCultures = cultures => {
  renderCultureSelect(cultures);
  const target = $("culturesListe");
  if (!target) return;
  target.innerHTML = table(
    ["Nom", "Type", "Description", "Gestion"],
    cultures.map(culture => [
      escapeHTML(culture.nom),
      escapeHTML(culture.type_culture),
      escapeHTML(culture.description || "—"),
      `<button class="btn btn-sm btn-outline-success" type="button" data-edit-culture="${escapeHTML(culture.id)}">Modifier</button>`
    ]),
    "Aucune culture enregistrée."
  );
};
const renderParcels = (parcels, cultures = []) => {
  window.culturesCourantes = cultures;
  renderParcelForms(parcels);
  renderCultures(cultures);
  const target = $("contenu");
  if (!target) return;
  target.innerHTML = parcels.length ? parcels.map(parcel => `
    <article class="parcel-block">
      <div class="d-flex justify-content-between align-items-start gap-2 flex-wrap">
        <div>
          <h3 class="h5 mb-1">${escapeHTML(parcel.nom)}</h3>
          <p class="text-muted mb-2">${escapeHTML(parcel.localisation || "")}</p>
          <p class="small mb-2">Superficie : ${escapeHTML(parcel.superficie ?? "—")}</p>
        </div>
        <button class="btn btn-sm btn-outline-success" type="button" data-edit-parcel="${escapeHTML(parcel.id)}">Modifier la parcelle</button>
      </div>
      ${table(["Zone", "Culture", "Gestion"], parcel.zones.map(zone => [
        escapeHTML(zone.nom), escapeHTML(zone.cultureNom || "Culture inconnue"),
        `<button class="btn btn-sm btn-outline-success" type="button" data-edit-zone="${escapeHTML(zone.id)}">Modifier</button>`
      ]), "Aucune zone enregistrée pour cette parcelle.")}
    </article>`).join("") : vide("Aucune parcelle enregistrée.");
};

const refreshMissionZones = parcels => {
  const select = $("missionZones");
  if (!select) return;
  const zones = parcels.flatMap(parcel => parcel.zones.map(zone => ({
    id: zone.id, label: labelZone({ ...zone, parcelleNom: parcel.nom })
  })));
  const signature = JSON.stringify(zones);
  if (select.dataset.signature !== signature) {
    const selected = new Set([...select.selectedOptions].map(option => option.value));
    select.innerHTML = zones.map(zone =>
      `<option value="${escapeHTML(zone.id)}"${selected.has(String(zone.id)) ? " selected" : ""}>${escapeHTML(zone.label)}</option>`
    ).join("");
    select.dataset.signature = signature;
  }
  renderMissionOrder();
};
function renderMissionOrder() {
  const order = $("missionOrder");
  const select = $("missionZones");
  if (!order || !select) return;
  order.innerHTML = [...select.selectedOptions].map(option => `<li>${escapeHTML(option.textContent)}</li>`).join("");
}
const moveMissionStep = direction => {
  const select = $("missionZones");
  if (!select) return;
  const selectedIndex = select.selectedIndex;
  const targetIndex = selectedIndex + direction;
  if (selectedIndex < 0 || targetIndex < 0 || targetIndex >= select.options.length) return;
  const options = [...select.options];
  const [option] = options.splice(selectedIndex, 1);
  options.splice(targetIndex, 0, option);
  options.forEach(item => select.append(item));
  option.selected = true;
  renderMissionOrder();
};
const renderMissionTable = missions => renderTable("tableau",
  ["Identifiant", "Date prévue / début", "Étapes dans l'ordre", "État", "Résultat reçu du robot"],
  [...missions].sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage)).map(mission => [
    escapeHTML(mission.mission_id), dateHeure(mission.horodatage),
    escapeHTML(Array.isArray(mission.zones) ? mission.zones.join(" → ") : mission.zones || "—"),
    badgeEtatMission(mission.etat), escapeHTML(mission.resultat || "En attente des données du robot")
  ]), "Aucune mission reçue ou planifiée.");

const renderConfigZones = (parcelles, configurations) => {
  const select = $("configZone");
  if (!select) return;
  const form = $("irrigationConfigForm");
  const zones = parcelles.flatMap(parcel => parcel.zones.map(zone => ({
    ...zone, parcelleNom: parcel.nom
  })));
  const selection = select.value;
  const signature = JSON.stringify(zones.map(zone => [zone.id, zone.nom, zone.parcelleNom]));
  if (select.dataset.signature !== signature) {
    select.innerHTML = `<option value="">Choisir une zone</option>${zones.map(zone =>
      `<option value="${escapeHTML(zone.id)}">${escapeHTML(labelZone(zone))}</option>`).join("")}`;
    select.dataset.signature = signature;
  }
  if (zones.some(zone => memeIdentifiant(zone.id, selection))) select.value = selection;
  if (form.dataset.loadedZone !== select.value) {
    const config = configurations.find(item => memeIdentifiant(item.zone, select.value));
    $("humidityThreshold").value = config?.seuil_humidite ?? "";
    $("maxDuration").value = config?.duree_max_secondes ?? "";
    $("maxVolume").value = config?.volume_max_litres ?? "";
    form.dataset.loadedZone = select.value;
  }
};

const renderPage = async () => {
  const [history, measures, irrigations, missions, incidents, robot, parcels, configurations] = await Promise.all([
    chargerHistorique(), chargerMesures(), chargerIrrigations(), chargerMissions(),
    chargerIncidents(), chargerEtatRobot(), chargerParcelles(), chargerConfigurationsIrrigation()
  ]);
  dernierHistorique = history;
  const sortedHistory = [...history].sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage));
  const humidity = measures.filter(record => record.type === "mesure_humidite" && isValidMeasure(record));
  const temperatures = measures.filter(record => record.type === "mesure_temperature" && isValidMeasure(record));
  const completed = missions.filter(mission => mission.etat === "terminee");
  const avgHumidity = humidity.length
    ? (humidity.reduce((sum, record) => sum + Number(record.valeur), 0) / humidity.length).toFixed(1) : "—";

  if (page === "index") {
    $("etat").innerHTML = badgeEtatRobot(robot.etat);
    $("derniereCom").textContent = dateHeure(robot.derniere_communication);
    $("nbParcelles").textContent = parcels.length;
    $("humMoy").textContent = avgHumidity;
    $("nbMissions").textContent = completed.length;
    renderChart("graph", [{ x: humidity.map(record => record.horodatage), y: humidity.map(record => Number(record.valeur)), type: "scatter", mode: "lines+markers", name: "Humidité", line: { color: "#2b6648" } }], { yaxis: { title: "Valeur brute" }, xaxis: { title: "Date et heure" } }, "Aucune mesure valide à afficher.");
    const recent = irrigations.filter(item => item.etat !== "interdit" && Date.now() - new Date(item.debut).getTime() <= 7 * 86400000);
    $("arrosagesRecents").textContent = recent.length;
    $("activites").innerHTML = sortedHistory.length ? sortedHistory.slice(0, 5).map(record =>
      `<div class="activity-row"><span>${badgeType(record.type)}<br><small class="text-muted">${dateHeure(record.horodatage)} · ${escapeHTML(record.zone || "—")}</small></span><span>${escapeHTML(record.mission_id || "")}</span></div>`
    ).join("") : vide("Aucun historique reçu.");
  }

  updateZoneCache(parcels, chargerParcelles.dernieresCultures || []);
  if (page === "parcelles") renderParcels(parcels, chargerParcelles.dernieresCultures || []);

  if (page === "robot") {
    $("etat").innerHTML = badgeEtatRobot(robot.etat);
    $("idr").textContent = robot.robot_id || "—";
    $("com").textContent = dateHeure(robot.derniere_communication);
    $("prob").textContent = robot.probleme || "Aucun problème signalé";
    const currentMission = missions.find(mission => mission.etat === "en_cours");
    $("mission").innerHTML = currentMission
      ? `${escapeHTML(currentMission.mission_id)} ${badgeEtatMission(currentMission.etat)}`
      : vide("Aucune mission en cours.");
    $("missionId").textContent = currentMission?.mission_id || "Aucune mission en cours";
    const lastArrival = sortedHistory.find(item => item.type === "arrivee_zone" &&
      (!currentMission || item.mission_id === currentMission.mission_id));
    $("currentZone").textContent = lastArrival?.zone || "Aucune zone signalée";
    if (currentMission) {
      const visited = new Set(sortedHistory.filter(item => item.type === "arrivee_zone" &&
        item.mission_id === currentMission.mission_id).map(item => item.zone));
      $("progress").textContent = `${visited.size} / ${currentMission.zones.length} zones signalées`;
    } else $("progress").textContent = "—";
    $("incidents").innerHTML = incidents.length ? incidents.slice().sort((a, b) =>
      new Date(b.horodatage) - new Date(a.horodatage)).map(item =>
      `<div class="py-2 border-bottom">${badgeType(item.type)} ${escapeHTML(item.detail || item.zone)} <small class="text-muted">${dateHeure(item.horodatage)}</small></div>`
    ).join("") : vide("Aucun incident signalé.");
  }

  if (page === "mesures") {
    renderChart("graphHumidity", [{ x: humidity.map(record => record.horodatage), y: humidity.map(record => Number(record.valeur)), type: "scatter", mode: "lines+markers", name: "Humidité", line: { color: "#2b6648" } }], { yaxis: { title: "Valeur brute" }, xaxis: { title: "Date et heure" } }, "Aucune mesure d'humidité valide.");
    renderChart("graphTemperature", [{ x: temperatures.map(record => record.horodatage), y: temperatures.map(record => Number(record.valeur)), type: "scatter", mode: "lines+markers", name: "Température", line: { color: "#2f80c9" } }], { yaxis: { title: "Température (°C)" }, xaxis: { title: "Date et heure" } }, "Aucune mesure de température valide.");
    const rows = measures.slice().sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage)).map(record => {
      const valid = isValidMeasure(record);
      const missing = record.valeur === null || record.valeur === undefined || record.valeur === "";
      const state = valid ? badge(["ok", "Valide"]) : badge(["err", missing ? "Manquante" : record.etat === "incoherent" ? "Incohérente" : "Invalide"]);
      return [dateHeure(record.horodatage), escapeHTML(record.zone || "—"), escapeHTML(TYPES[record.type] || record.type),
        valid ? escapeHTML(record.valeur) : (missing ? "—" : escapeHTML(record.valeur)),
        record.type === "mesure_humidite" ? "Valeur brute" : escapeHTML(record.unite || "—"), state];
    });
    renderTable("tableau", ["Date et heure", "Zone", "Mesure", "Valeur reçue", "Unité", "État"], rows, "Aucune mesure reçue.");
  }

  if (page === "missions") {
    refreshMissionZones(parcels);
    renderMissionTable(missions);
  }

  if (page === "irrigation") {
    renderConfigZones(parcels, configurations);
    const latestByZone = new Map();
    humidity.slice().sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage)).forEach(record => {
      if (!latestByZone.has(record.zone)) latestByZone.set(record.zone, record);
    });
    const recommendations = parcels.flatMap(parcel => parcel.zones.map(zone => {
      const config = configurations.find(item => memeIdentifiant(item.zone, zone.id));
      const reading = latestByZone.get(zone.nom);
      return { zone, parcel, config, reading };
    })).filter(item => item.reading && item.config && Number(item.reading.valeur) < Number(item.config.seuil_humidite));
    $("recommendations").innerHTML = recommendations.length
      ? `<ul class="mb-0">${recommendations.map(item => `<li>${escapeHTML(labelZone({ ...item.zone, parcelleNom: item.parcel.nom }))} : ${valeurBrute(item.reading.valeur)} (seuil ${escapeHTML(item.config.seuil_humidite)}), arrosage recommandé selon la mesure reçue.</li>`).join("")}</ul>`
      : vide("Aucune recommandation calculable : vérifiez les mesures reçues et configurez les seuils par zone.");
    const totalVolume = irrigations.reduce((sum, item) => sum + (numeric(item.volume) ? Number(item.volume) : 0), 0);
    const lastWatering = irrigations.find(item => item.etat !== "interdit");
    const recent = irrigations.filter(item => item.etat !== "interdit" && Date.now() - new Date(item.debut).getTime() <= 7 * 86400000);
    $("lastWatering").innerHTML = lastWatering ? `${escapeHTML(lastWatering.zone)}<br><small>${dateHeure(lastWatering.debut)}</small>` : "Aucun arrosage reçu";
    $("wateringCount").textContent = recent.length;
    $("waterVolume").textContent = irrigations.some(item => numeric(item.volume)) ? `${totalVolume.toFixed(1)} L` : "Non communiqué";
    const recorded = irrigations.filter(item => item.etat !== "interdit");
    renderChart("irrigationGraph", [{ x: recorded.filter(item => numeric(item.duree)).map(item => item.debut), y: recorded.filter(item => numeric(item.duree)).map(item => Number(item.duree)), type: "bar", name: "Durée (s)", marker: { color: "#8bc34a" } }], { yaxis: { title: "Durée (s)" }, xaxis: { title: "Date et heure" } }, "Aucun arrosage reçu.");
    const irrigated = irrigations.filter(item => item.etat !== "interdit" && (numeric(item.humidite_avant) || numeric(item.humidite_apres)));
    renderChart("humidityWateringGraph", [
      { x: irrigated.map(item => item.debut), y: irrigated.map(item => numeric(item.humidite_avant) ? Number(item.humidite_avant) : null), type: "scatter", mode: "lines+markers", name: "Avant", line: { color: "#2f80c9" } },
      { x: irrigated.map(item => item.debut), y: irrigated.map(item => numeric(item.humidite_apres) ? Number(item.humidite_apres) : null), type: "scatter", mode: "lines+markers", name: "Après", line: { color: "#2b6648" } }
    ], { yaxis: { title: "Humidité (valeur brute)" }, xaxis: { title: "Date et heure" } }, "Aucune mesure d'humidité avant/après disponible.");
    renderTable("tableau", ["Début", "Fin", "Zone", "Durée", "Volume", "Humidité avant", "Température avant", "Décision"],
      irrigations.map(item => [
        dateHeure(item.debut), dateHeure(item.fin), escapeHTML(item.zone), numeric(item.duree) ? `${escapeHTML(item.duree)} s` : "—",
        numeric(item.volume) ? `${escapeHTML(item.volume)} L` : "—", valeurBrute(item.humidite_avant),
        numeric(item.temperature_avant) ? `${escapeHTML(item.temperature_avant)} °C` : "—",
        badge(item.decision === "interdit" ? ["err", "Interdit : mesure invalide"] : item.decision === "recommande" ? ["cours", "Recommandé"] : ["ok", "Effectué"])
      ]), "Aucun historique d'arrosage reçu.");
  }

  if (page === "incidents") {
    renderTable("tableau", ["Date et heure", "Type", "Zone", "Mission", "Détail"],
      incidents.slice().sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage)).map(item => [
        dateHeure(item.horodatage), badgeType(item.type), escapeHTML(item.zone || "—"),
        escapeHTML(item.mission_id || "—"), escapeHTML(item.detail || "—")
      ]), "Aucun incident signalé.");
  }

  if (page === "historique") {
    const typeSelect = $("historyType");
    const zoneSelect = $("historyZone");
    const selectedType = typeSelect.value;
    const selectedZone = zoneSelect.value;
    typeSelect.innerHTML = `<option value="">Tous les types</option>${Object.entries(TYPES).map(([type, label]) =>
      `<option value="${type}">${escapeHTML(label)}</option>`).join("")}`;
    zoneSelect.innerHTML = `<option value="">Toutes les zones</option>${[...new Set(history.map(item => item.zone).filter(Boolean))].sort().map(zone =>
      `<option value="${escapeHTML(zone)}">${escapeHTML(zone)}</option>`).join("")}`;
    typeSelect.value = selectedType;
    zoneSelect.value = selectedZone;
    renderHistory(history);
  }

  if (page === "rapports") {
    const finishedRate = missions.length ? (completed.length / missions.length * 100).toFixed(1) : "—";
    const durations = missions.filter(mission => mission.fin && mission.horodatage)
      .map(mission => (new Date(mission.fin) - new Date(mission.horodatage)) / 60000).filter(Number.isFinite);
    const avgDuration = durations.length ? `${(durations.reduce((sum, value) => sum + value, 0) / durations.length).toFixed(1)} min` : "—";
    const waterVolume = irrigations.reduce((sum, item) => sum + (numeric(item.volume) ? Number(item.volume) : 0), 0);
    const validRate = measures.length ? `${(measures.filter(isValidMeasure).length / measures.length * 100).toFixed(1)} %` : "—";
    $("nbInc").textContent = incidents.length;
    $("validRate").textContent = validRate;
    $("tauxMissions").textContent = `${finishedRate}${finishedRate === "—" ? "" : " %"}`;
    $("dureeMoyenne").textContent = avgDuration;
    $("volumeRapport").textContent = irrigations.some(item => numeric(item.volume)) ? `${waterVolume.toFixed(1)} L` : "Non communiqué";
    $("stats").innerHTML = ["planifiee", "en_cours", "terminee", "interrompue"].map(state =>
      `<div class="d-flex justify-content-between py-1"><span>${ETAT_MISSION[state][1]}</span><strong>${missions.filter(mission => mission.etat === state).length}</strong></div>`
    ).join("");
    renderChart("graph", [{ x: humidity.map(record => record.horodatage), y: humidity.map(record => Number(record.valeur)), type: "scatter", mode: "lines+markers", name: "Humidité", line: { color: "#2b6648" } }], { yaxis: { title: "Valeur brute" }, xaxis: { title: "Date et heure" } }, "Aucune mesure valide à afficher.");
    const zones = [...new Set(humidity.map(record => record.zone))];
    renderChart("graphZones", [{ x: zones, y: zones.map(zone => {
      const values = humidity.filter(record => record.zone === zone).map(record => Number(record.valeur));
      return values.reduce((sum, value) => sum + value, 0) / values.length;
    }), type: "bar", marker: { color: "#8bc34a" }, name: "Valeur brute moyenne" }], { yaxis: { title: "Valeur brute moyenne" } }, "Aucune donnée de mesure par zone.");
  }
  $("lastUpdate").textContent = `Dernière mise à jour : ${dateHeure(new Date().toISOString())}`;
  $("loadError")?.remove();
};

// Les écritures ci-dessous gèrent les données de l'application; aucune n'envoie
// une commande de mouvement, d'arrêt ou d'arrosage au robot.
$("parcelForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const saved = await enregistrerParcelle({
      id: $("parcelId").value || undefined,
      nom: $("parcelName").value.trim(),
      superficie: $("parcelArea").value,
      localisation: $("parcelLocation").value.trim()
    });
    form.reset(); $("parcelId").value = ""; $("cancelParcelEdit").classList.add("d-none");
    showFormMessage(form, `Parcelle « ${saved.nom} » enregistrée.`, true);
    await renderPage();
  } catch (error) {
    console.error(error);
    showFormMessage(form, messageErreurFormulaire(error, "La parcelle n'a pas pu être enregistrée."));
  }
});
$("cancelParcelEdit")?.addEventListener("click", () => {
  $("parcelForm").reset(); $("parcelId").value = ""; $("cancelParcelEdit").classList.add("d-none");
  resetFormFeedback($("parcelForm"));
});
const remplirFormulaireParcelle = parcel => {
  $("parcelId").value = parcel.id;
  $("parcelName").value = parcel.nom;
  $("parcelArea").value = parcel.superficie ?? "";
  $("parcelLocation").value = parcel.localisation || "";
  $("cancelParcelEdit").classList.remove("d-none");
  $("parcelName").focus();
};
const remplirFormulaireZone = zone => {
  $("zoneId").value = zone.id;
  $("zoneParcel").value = String(zone.parcelle);
  $("zoneName").value = zone.nom;
  $("zoneCulture").value = String(zone.culture);
  $("cancelZoneEdit").classList.remove("d-none");
  $("zoneName").focus();
};
const remplirFormulaireCulture = culture => {
  $("cultureId").value = culture.id;
  $("cultureName").value = culture.nom;
  $("cultureType").value = culture.type_culture;
  $("cultureDescription").value = culture.description || "";
  $("cancelCultureEdit").classList.remove("d-none");
  $("cultureName").focus();
};
$("contenu")?.addEventListener("click", event => {
  const parcelButton = event.target.closest("[data-edit-parcel]");
  const zoneButton = event.target.closest("[data-edit-zone]");
  if (parcelButton) {
    const parcel = window.parcellesCourantes.find(item => memeIdentifiant(item.id, parcelButton.dataset.editParcel));
    if (!parcel) return;
    remplirFormulaireParcelle(parcel);
  }
  if (zoneButton) {
    const zone = window.zonesCourantes.find(item => memeIdentifiant(item.id, zoneButton.dataset.editZone));
    if (!zone) return;
    remplirFormulaireZone(zone);
  }
});
$("culturesListe")?.addEventListener("click", event => {
  const cultureButton = event.target.closest("[data-edit-culture]");
  if (!cultureButton) return;
  const culture = window.culturesCourantes.find(item => memeIdentifiant(item.id, cultureButton.dataset.editCulture));
  if (!culture) return;
  remplirFormulaireCulture(culture);
});
$("zoneForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const saved = await enregistrerZone({
      id: $("zoneId").value || undefined,
      parcelle: $("zoneParcel").value,
      nom: $("zoneName").value.trim(),
      culture: $("zoneCulture").value
    });
    form.reset(); $("zoneId").value = ""; $("cancelZoneEdit").classList.add("d-none");
    showFormMessage(form, `Zone « ${saved.nom} » enregistrée.`, true);
    await renderPage();
  } catch (error) {
    console.error(error);
    showFormMessage(form, messageErreurFormulaire(error, "La zone n'a pas pu être enregistrée."));
  }
});
$("cancelZoneEdit")?.addEventListener("click", () => {
  $("zoneForm").reset(); $("zoneId").value = ""; $("cancelZoneEdit").classList.add("d-none");
  resetFormFeedback($("zoneForm"));
});
$("cultureForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const saved = await enregistrerCulture({
      id: $("cultureId").value || undefined,
      nom: $("cultureName").value.trim(),
      type_culture: $("cultureType").value.trim(),
      description: $("cultureDescription").value.trim()
    });
    form.reset(); $("cultureId").value = ""; $("cancelCultureEdit").classList.add("d-none");
    showFormMessage(form, `Culture « ${saved.nom} » enregistrée.`, true);
    await renderPage();
  } catch (error) {
    console.error(error);
    showFormMessage(form, messageErreurFormulaire(error, "La culture n'a pas pu être enregistrée."));
  }
});
$("cancelCultureEdit")?.addEventListener("click", () => {
  $("cultureForm").reset(); $("cultureId").value = ""; $("cancelCultureEdit").classList.add("d-none");
  resetFormFeedback($("cultureForm"));
});

$("missionZones")?.addEventListener("change", renderMissionOrder);
$("moveStepUp")?.addEventListener("click", () => moveMissionStep(-1));
$("moveStepDown")?.addEventListener("click", () => moveMissionStep(1));
$("missionForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const selected = [...$("missionZones").selectedOptions];
  if (!selected.length) { $("missionZones").focus(); return; }
  try {
    const zoneNames = selected.map(option => {
      const zone = window.zonesCourantes.find(item => memeIdentifiant(item.id, option.value));
      return zone ? labelZone(zone) : option.textContent;
    });
    const mission = await enregistrerMission({
      horodatage: new Date($("missionDate").value).toISOString(),
      zones: zoneNames
    });
    form.reset(); $("missionZones").selectedIndex = -1; renderMissionOrder();
    showFormMessage(form, `Mission ${mission.mission_id} planifiée localement. Elle n'a pas été envoyée au robot.`, true);
    await renderPage();
  } catch (error) { console.error(error); showFormMessage(form, "La mission n'a pas pu être enregistrée."); }
});

$("configZone")?.addEventListener("change", async () => {
  try { renderConfigZones(await chargerParcelles(), await chargerConfigurationsIrrigation()); }
  catch (error) { showLoadError(error); }
});
$("irrigationConfigForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const saved = await enregistrerConfigurationIrrigation({
      zone: $("configZone").value,
      seuil_humidite: Number($("humidityThreshold").value),
      duree_max_secondes: Number($("maxDuration").value),
      volume_max_litres: $("maxVolume").value === "" ? null : Number($("maxVolume").value)
    });
    showFormMessage(form, `Configuration de ${saved.zone} enregistrée sur cet appareil. Elle ne modifie pas le robot.`, true);
    form.dataset.loadedZone = "";
    await renderPage();
  } catch (error) { console.error(error); showFormMessage(form, "La configuration n'a pas pu être enregistrée."); }
});

const afficherSession = utilisateur => {
  const cible = $("sessionUser");
  if (!cible || !utilisateur) return;
  const nom = [utilisateur.first_name, utilisateur.last_name].filter(Boolean).join(" ") || utilisateur.username;
  const roles = Array.isArray(utilisateur.groups) && utilisateur.groups.length
    ? utilisateur.groups.join(", ") : (utilisateur.is_staff ? "Administrateur" : "Utilisateur");
  cible.textContent = `${nom} · ${roles}`;
};

const deconnecter = async () => {
  const csrf = jetonCSRF();
  if (!csrf) {
    showLoadError(new ErreurAPI(
      "Jeton CSRF introuvable. Rechargez la page depuis Django avant de vous déconnecter.",
      { statut: 403 }
    ));
    return;
  }
  try {
    const response = await fetch("/deconnexion/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": csrf,
        Accept: "text/html"
      }
    });
    if (!response.ok && response.status !== 302) {
      throw new ErreurAPI("La déconnexion a été refusée par le serveur.", { statut: response.status });
    }
  } catch (error) {
    console.error(error);
    showLoadError(error instanceof ErreurAPI ? error : new ErreurAPI(
      "Impossible de se déconnecter. Vérifiez que Django est démarré.",
      { statut: 0 }
    ));
    return;
  }
  window.location.assign("/connexion/");
};
$("logoutButton")?.addEventListener("click", deconnecter);

const refreshPage = async () => {
  try { await renderPage(); }
  catch (error) { showLoadError(error); }
};

const demarrerApplication = async () => {
  try {
    const utilisateur = await verifierSession();
    if (!utilisateur) {
      redirigerVersConnexion();
      return;
    }
    afficherSession(utilisateur);
    await refreshPage();
    window.setInterval(refreshPage, 10000);
  } catch (error) { showLoadError(error); }
};
demarrerApplication();
