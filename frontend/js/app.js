// Navigation, formulaires de gestion et affichage des données reçues.
// Les pages partagent ce script et indiquent leur vue avec body[data-page].
const MENU = [
  ["index", "grid", "Tableau de bord", "dashboard.html"],
  ["parcelles", "map", "Mes parcelles", "parcelles.html"],
  ["pilotage", "controller", "Pilotage du robot et autres", "pilotage.html"],
  ["robot", "robot", "État du robot", "robot.html"],
  ["mesures", "droplet", "Humidité du sol", "mesures.html"],
  ["missions", "flag", "Missions et opérations", "missions.html"],
  ["irrigation", "moisture", "Irrigation", "irrigation.html"],
  ["incidents", "exclamation-triangle", "Alertes et incidents", "incidents.html"],
  ["historique", "clock-history", "Historique", "historique.html"],
  ["rapports", "bar-chart", "Rapports et statistiques", "rapports.html"],
  ["documentation", "book", "Documentation", "/documentation/"]
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
  annulee: ["off", "Annulée"], terminee: ["ok", "Terminée"], interrompue: ["err", "Interrompue"]
};
const TYPES = {
  operation_irrigation: "Opération d’irrigation", demarrage_mission: "Démarrage de mission", deplacement: "Déplacement",
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

// Petits formateurs communs : états, dates, tableaux, graphiques et messages.
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
    main.prepend(alert);
  }
  alert.textContent = `${error.message || "Actualisation impossible."} Nouvelle tentative dans 10 secondes. Les valeurs précédentes peuvent être périmées.`;
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

// La navigation et le pied de page sont injectés pour être identiques sur les pages.
document.body.insertAdjacentHTML("afterbegin", `<nav class="sidebar" id="sidebar" aria-label="Navigation principale">
  <a class="brand" href="index.html"><i class="bi bi-flower1" aria-hidden="true"></i><span>RoboAgri <strong>Kin</strong></span></a>
  <a class="sidebar-home" href="index.html"><i class="bi bi-house" aria-hidden="true"></i> Accueil</a>
  <span class="sidebar-label">SUPERVISION</span>
  ${MENU.map(([key, icon, label, href]) => `<a href="${href}" class="${key === page ? "active" : ""}"${key === page ? ' aria-current="page"' : ""}><i class="bi bi-${icon}" aria-hidden="true"></i> ${label}</a>`).join("")}
  <p class="sidebar-note">Données du serveur. Les missions préparées ne sont pas envoyées automatiquement au robot.</p>
<span id="sessionUser" class="sidebar-note"></span><button class="btn btn-outline-light mt-2" id="logoutButton" type="button">Se déconnecter</button></nav>`);
const main = document.querySelector("main");
main.insertAdjacentHTML("afterbegin", `<div class="topbar-mobile"><button class="btn btn-outline-secondary" id="menuToggle" type="button" aria-controls="sidebar" aria-expanded="false" aria-label="Ouvrir le menu"><i class="bi bi-list" aria-hidden="true"></i></button><strong>RoboAgri-Kin</strong></div>`);
document.body.insertAdjacentHTML("beforeend", `<footer class="app-footer" id="appFooter"><span>Les mesures et états du robot sont affichés en lecture seule.</span><span id="lastUpdate">Dernière mise à jour : en attente</span></footer>`);
$("menuToggle")?.addEventListener("click", event => {
  const expanded = $("sidebar").classList.toggle("open");
  event.currentTarget.setAttribute("aria-expanded", String(expanded));
});


let dernierHistorique = [];
let derniereZoneOptions = "";

// Normalise les libellés et les données de mesure utilisés par plusieurs vues.
const findZone = (parcelles, zoneId) => parcelles.flatMap(parcelle =>
  parcelle.zones.map(zone => ({ ...zone, parcelleNom: parcelle.nom }))
).find(zone => zone.id === zoneId);
const labelZone = zone => zone ? `${zone.parcelleNom} · ${zone.nom}` : "Zone inconnue";
const isValidMeasure = record => record.etat === "valide" && numeric(record.valeur) &&
  (record.type !== "mesure_humidite" || Number(record.valeur) >= 0);

// Filtre le journal sans perdre les choix pendant le rafraîchissement périodique.
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

// Met à jour les listes et tableaux de parcelles avec la mesure la plus récente.
const renderParcelForms = parcels => {
  const select = $("zoneParcel");
  if (!select) return;
  const selected = select.value;
  select.innerHTML = `<option value="">Choisir une parcelle</option>${parcels.map(parcel =>
    `<option value="${escapeHTML(parcel.id)}">${escapeHTML(parcel.nom)}</option>`).join("")}`;
  if (parcels.some(parcel => parcel.id === selected)) select.value = selected;
};
const renderParcels = (parcels, humidity = []) => {
  renderParcelForms(parcels);
  const target = $("contenu");
  if (!target) return;
  const readingsByZone = new Map();
  humidity.slice().sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage)).forEach(record => {
    if (!readingsByZone.has(record.zone)) readingsByZone.set(record.zone, record);
  });
  target.innerHTML = parcels.length ? parcels.map(parcel => `
    <article class="parcel-block">
      <div class="d-flex justify-content-between align-items-start gap-2 flex-wrap">
        <div><h3 class="h5 mb-1">${escapeHTML(parcel.nom)}</h3><p class="text-muted mb-2">${escapeHTML(parcel.lieu)}</p></div>
        <button class="btn btn-sm btn-outline-success" type="button" data-edit-parcel="${escapeHTML(parcel.id)}">Modifier la parcelle</button>
      </div>
      ${table(["Zone", "Culture", "Humidité reçue", "Gestion"], parcel.zones.map(zone => [
        escapeHTML(zone.nom), escapeHTML(zone.culture),
        valeurBrute(readingsByZone.get(labelZone({...zone, parcelleNom: parcel.nom}))?.valeur),
        `<button class="btn btn-sm btn-outline-success" type="button" data-edit-zone="${escapeHTML(zone.id)}">Modifier</button>`
      ]), "Aucune zone enregistrée pour cette parcelle.")}
    </article>`).join("") : vide("Aucune parcelle enregistrée.");
};

// Présente les zones dans l'ordre choisi avant l’enregistrement de la mission sur le serveur.
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
      `<option value="${escapeHTML(zone.id)}"${selected.has(zone.id) ? " selected" : ""}>${escapeHTML(zone.label)}</option>`
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

// Charge les données communes, puis ne dessine que les composants de la page courante.
const renderPage = async () => {
  const [history, measures, irrigations, missions, incidents, robot, parcels] = await Promise.all([
    chargerHistorique(), chargerMesures(), chargerIrrigations(), chargerMissions(),
    chargerIncidents(), chargerEtatRobot(), chargerParcelles()
  ]);
  updateZoneCache(parcels);
  remplirSelect('zoneCulture', donneesServeur.cultures);
  remplirSelect('missionRobot', donneesServeur.robots);
  remplirSelect('robotSelect', donneesServeur.robots);
  if ($('robotSelect')) $('robotSelect').value = robot.id;
  dernierHistorique = history;
  const sortedHistory = [...history].sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage));
  const humidity = measures.filter(record => record.type === "mesure_humidite" && isValidMeasure(record));
  const temperatures = measures.filter(record => record.type === "mesure_temperature" && isValidMeasure(record));
  const completed = missions.filter(mission => mission.etat === "terminee");
  const avgHumidity = humidity.length
    ? (humidity.reduce((sum, record) => sum + Number(record.valeur), 0) / humidity.length).toFixed(1) : "—";

  if (page === "index") {
    $("etat").innerHTML = badgeEtatRobot(robot.etat);
    $("derniereCom").textContent = `Dernière communication : ${dateHeure(robot.derniere_communication)}`;
    $("batteryLevel").textContent = numeric(robot.niveau_batterie) ? `${escapeHTML(robot.niveau_batterie)} %` : "Non communiqué";
    $("nbMissions").textContent = completed.length;
    $("humMoy").textContent = avgHumidity;
    $("robotSummary").innerHTML = `${badgeEtatRobot(robot.etat)}<span>${escapeHTML(robot.probleme || "Aucun problème signalé")}</span>`;
    $("robotPosition").textContent = robot.position || "Non communiquée";
    $("robotSpeed").textContent = numeric(robot.vitesse) ? `${escapeHTML(robot.vitesse)} km/h` : "Non communiquée";
    renderChart("graph", [{ x: humidity.map(record => record.horodatage), y: humidity.map(record => Number(record.valeur)), type: "scatter", mode: "lines+markers", name: "Humidité", line: { color: "#527c62", width: 3 }, marker: { color: "#183d32", size: 7 }, fill: "tozeroy", fillcolor: "rgba(82,124,98,0.10)" }], { yaxis: { title: "Valeur brute", gridcolor: "#edf1ed" }, xaxis: { title: "Date et heure", gridcolor: "#edf1ed" } }, "Aucune mesure valide à afficher.");
    const readingsByZone = new Map();
    humidity.slice().sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage)).forEach(record => {
      if (!readingsByZone.has(record.zone)) readingsByZone.set(record.zone, record);
    });
    $("zonesOverview").innerHTML = parcels.length ? parcels.map(parcel => `
      <article class="zone-parcel">
        <div class="zone-parcel-heading"><span><i class="bi bi-geo-alt" aria-hidden="true"></i> ${escapeHTML(parcel.nom)}</span><small>${escapeHTML(parcel.lieu)}</small></div>
        ${parcel.zones.length ? parcel.zones.map(zone => {
          const reading = readingsByZone.get(labelZone({...zone, parcelleNom: parcel.nom}));
          const value = reading ? Number(reading.valeur) : null;

          return `<div class="zone-reading"><span>${escapeHTML(zone.nom)}<small>${escapeHTML(zone.culture)}</small></span><strong>${value === null ? "—" : `${escapeHTML(value)} <small>brut</small>`}</strong></div>`;
        }).join("") : vide("Aucune zone enregistrée.") }
      </article>`).join("") : vide("Aucune parcelle enregistrée.");
    const recentIncidents = incidents.slice().sort((a, b) => new Date(b.horodatage) - new Date(a.horodatage)).slice(0, 3);
    $("alertOverview").innerHTML = recentIncidents.length ? recentIncidents.map(item =>
      `<div class="alert-row"><span class="alert-row-icon"><i class="bi bi-exclamation-triangle" aria-hidden="true"></i></span><span><strong>${escapeHTML(TYPES[item.type] || item.type)}</strong><small>${escapeHTML(item.detail || item.zone || "Événement signalé")} · ${dateHeure(item.horodatage)}</small></span></div>`
    ).join("") : vide("Aucune alerte signalée.");
    $("activites").innerHTML = sortedHistory.length ? sortedHistory.slice(0, 5).map(record =>
      `<div class="activity-row"><span>${badgeType(record.type)}<br><small class="text-muted">${dateHeure(record.horodatage)} · ${escapeHTML(record.zone || "—")}</small></span><span>${escapeHTML(record.mission_id || "")}</span></div>`
    ).join("") : vide("Aucun historique reçu.");
  }

  if (page === "parcelles") renderParcels(parcels, humidity);

  if (page === "robot") {
    $("etat").innerHTML = badgeEtatRobot(robot.etat);
    $("idr").textContent = robot.robot_id || "—";
    $("com").textContent = dateHeure(robot.derniere_communication);
    $("prob").textContent = robot.probleme || "Aucun problème signalé";
    $("robotBattery") && ($("robotBattery").textContent = numeric(robot.niveau_batterie) ? `${robot.niveau_batterie} %` : "Non communiqué");
    $("robotPositionDetail") && ($("robotPositionDetail").textContent = robot.position || "Non communiquée");
    $("robotSpeedDetail") && ($("robotSpeedDetail").textContent = numeric(robot.vitesse) ? `${robot.vitesse} km/h` : "Non communiquée");
    $("robotSensors") && ($("robotSensors").textContent = robot.capteurs || "État non communiqué");
    const currentMission = missions.find(mission => mission.etat === "en_cours" && mission.robot_id === robot.id);
    $("mission").innerHTML = currentMission
      ? `${escapeHTML(currentMission.mission_id)} ${badgeEtatMission(currentMission.etat)}`
      : vide("Aucune mission en cours.");
    $("missionId").textContent = currentMission?.mission_id || "Aucune mission en cours";
    const lastArrival = sortedHistory.find(item => item.type === "arrivee_zone" && item.robot_id === robot.id &&
      (!currentMission || item.mission_id === currentMission.mission_id));
    $("currentZone").textContent = lastArrival?.zone || "Aucune zone signalée";
    if (currentMission) {
      const visited = new Set(sortedHistory.filter(item => item.type === "arrivee_zone" &&
        item.mission_id === currentMission.mission_id).map(item => item.zone));
      $("progress").textContent = `${visited.size} / ${currentMission.zones.length} zones signalées`;
    } else $("progress").textContent = "—";
    const robotIncidents = incidents.filter(item => item.robot_id === robot.id);
    $("incidents").innerHTML = robotIncidents.length ? robotIncidents.slice().sort((a, b) =>
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
    const totalVolume = irrigations.reduce((sum, item) => sum + (numeric(item.volume) ? Number(item.volume) : 0), 0);
    const lastWatering = irrigations.find(item => item.etat === "executee");
    $("lastWatering").innerHTML = lastWatering ? `${escapeHTML(lastWatering.zone)}<br><small>${dateHeure(lastWatering.debut)}</small>` : "Aucun arrosage reçu";
    $("wateringCount").textContent = irrigations.filter(item => item.etat === "executee").length;
    $("waterVolume").textContent = irrigations.some(item => numeric(item.volume)) ? `${totalVolume.toFixed(1)} L` : "Non communiqué";
    const recorded = irrigations.filter(item => item.etat === "executee");
    renderChart("irrigationGraph", [{ x: recorded.filter(item => numeric(item.duree)).map(item => item.debut), y: recorded.filter(item => numeric(item.duree)).map(item => Number(item.duree)), type: "bar", name: "Durée (s)", marker: { color: "#8bc34a" } }], { yaxis: { title: "Durée (s)" }, xaxis: { title: "Date et heure" } }, "Aucun arrosage reçu.");
    const irrigated = irrigations.filter(item => item.etat === "executee" && (numeric(item.humidite_avant) || numeric(item.humidite_apres)));
    renderChart("humidityWateringGraph", [
      { x: irrigated.map(item => item.debut), y: irrigated.map(item => numeric(item.humidite_avant) ? Number(item.humidite_avant) : null), type: "scatter", mode: "lines+markers", name: "Avant", line: { color: "#2f80c9" } },
      { x: irrigated.map(item => item.debut), y: irrigated.map(item => numeric(item.humidite_apres) ? Number(item.humidite_apres) : null), type: "scatter", mode: "lines+markers", name: "Après", line: { color: "#2b6648" } }
    ], { yaxis: { title: "Humidité (valeur brute)" }, xaxis: { title: "Date et heure" } }, "Aucune mesure d'humidité avant/après disponible.");
    renderTable("tableau", ["Opération créée le", "Fin communiquée", "Zone", "Durée", "Volume", "Humidité avant", "Température avant", "Résultat rapporté"],
      irrigations.map(item => [
        dateHeure(item.debut), dateHeure(item.fin), escapeHTML(item.zone), numeric(item.duree) ? `${escapeHTML(item.duree)} s` : "—",
        numeric(item.volume) ? `${escapeHTML(item.volume)} L` : "—", valeurBrute(item.humidite_avant),
        numeric(item.temperature_avant) ? `${escapeHTML(item.temperature_avant)} °C` : "—",
        badgeEtatIrrigation(item.etat)
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
    const durations = missions.filter(mission => mission.fin && mission.debut)
      .map(mission => (new Date(mission.fin) - new Date(mission.debut)) / 60000).filter(Number.isFinite);
    const avgDuration = durations.length ? `${(durations.reduce((sum, value) => sum + value, 0) / durations.length).toFixed(1)} min` : "—";
    const waterVolume = irrigations.reduce((sum, item) => sum + (numeric(item.volume) ? Number(item.volume) : 0), 0);
    const validRate = measures.length ? `${(measures.filter(isValidMeasure).length / measures.length * 100).toFixed(1)} %` : "—";
    $("nbInc").textContent = incidents.length;
    $("validRate").textContent = validRate;
    $("tauxMissions").textContent = `${finishedRate}${finishedRate === "—" ? "" : " %"}`;
    $("dureeMoyenne").textContent = avgDuration;
    $("volumeRapport").textContent = irrigations.some(item => numeric(item.volume)) ? `${waterVolume.toFixed(1)} L` : "Non communiqué";
    $("stats").innerHTML = ["planifiee", "en_cours", "terminee", "interrompue", "annulee"].map(state =>
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
// Les formulaires de parcelle et de zone enregistrent et modifient les données du serveur.
$("parcelForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const saved = await enregistrerParcelle({
      id: $("parcelId").value || undefined,
      nom: $("parcelName").value.trim(),
      lieu: $("parcelLocation").value.trim(), superficie: $("parcelArea").value
    });
    form.reset(); $("parcelId").value = ""; $("cancelParcelEdit").classList.add("d-none");
    showFormMessage(form, `Parcelle « ${saved.nom} » enregistrée sur le serveur.`, true);
    await refreshPage();
  } catch (error) { console.error(error); showFormMessage(form, error.message); } finally { libererFormulaire(form); }
});
$("cancelParcelEdit")?.addEventListener("click", () => {
  $("parcelForm").reset(); $("parcelId").value = ""; $("cancelParcelEdit").classList.add("d-none");
  resetFormFeedback($("parcelForm"));
});
$("contenu")?.addEventListener("click", event => {
  const parcelButton = event.target.closest("[data-edit-parcel]");
  const zoneButton = event.target.closest("[data-edit-zone]");
  if (parcelButton) {
    const parcel = window.parcellesCourantes.find(item => item.id === parcelButton.dataset.editParcel);
    if (!parcel) return;
    $("parcelId").value = parcel.id; $("parcelName").value = parcel.nom; $("parcelLocation").value = parcel.lieu; $("parcelArea").value = parcel.superficie;
    $("cancelParcelEdit").classList.remove("d-none"); $("parcelName").focus();
  }
  if (zoneButton) {
    const zone = window.zonesCourantes.find(item => item.id === zoneButton.dataset.editZone);
    if (!zone) return;
    $("zoneId").value = zone.id; $("zoneParcel").value = zone.parcelle_id;
    $("zoneName").value = zone.nom; $("zoneCulture").value = zone.culture_id;
    $("cancelZoneEdit").classList.remove("d-none"); $("zoneName").focus();
  }
});
$("zoneForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const saved = await enregistrerZone({
      id: $("zoneId").value || undefined, parcelle_id: $("zoneParcel").value,
      nom: $("zoneName").value.trim(), culture: $("zoneCulture").value.trim()
    });
    form.reset(); $("zoneId").value = ""; $("cancelZoneEdit").classList.add("d-none");
    showFormMessage(form, `Zone « ${saved.nom} » enregistrée sur le serveur.`, true);
    await refreshPage();
  } catch (error) { console.error(error); showFormMessage(form, error.message); } finally { libererFormulaire(form); }
});
$("cancelZoneEdit")?.addEventListener("click", () => {
  $("zoneForm").reset(); $("zoneId").value = ""; $("cancelZoneEdit").classList.add("d-none");
  resetFormFeedback($("zoneForm"));
});
const updateZoneCache = parcels => {
  window.parcellesCourantes = parcels;
  window.zonesCourantes = parcels.flatMap(parcel =>
    parcel.zones.map(zone => ({ ...zone, parcelleNom: parcel.nom })));
};

// Les zones sélectionnées servent à préparer une mission sur le serveur, pas à piloter le robot.
$("missionZones")?.addEventListener("change", renderMissionOrder);
$("moveStepUp")?.addEventListener("click", () => moveMissionStep(-1));
$("moveStepDown")?.addEventListener("click", () => moveMissionStep(1));
$("missionForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const selected = [...$("missionZones").selectedOptions];
  if (!selected.length) { $("missionZones").focus(); libererFormulaire(form); return; }
  try {
    const mission = await enregistrerMission({
      horodatage: new Date($("missionDate").value).toISOString(),
      zones: selected.map(option => option.value), robot: $("missionRobot").value
    });
    form.reset(); $("missionZones").selectedIndex = -1; renderMissionOrder();
    showFormMessage(form, `Mission ${mission.mission_id} enregistrée sur le serveur. Elle n'a pas été envoyée au robot.`, true);
    await refreshPage();
  } catch (error) { console.error(error); showFormMessage(form, error.message); } finally { libererFormulaire(form); }
});

// Chaque rafraîchissement relit les données de la couche api.js toutes les 10 secondes.
let actualisationEnCours = false;
let minuterieActualisation;
const refreshPage = async () => {
  if (actualisationEnCours || window.deconnexionEnCours) return;
  actualisationEnCours = true;
  try {
    await actualiserDonnees();
    const parcels = await chargerParcelles();
    updateZoneCache(parcels);
    await renderPage();
  } catch (error) { showLoadError(error); } finally { actualisationEnCours = false; }
};
const demarrer = async () => {
  try {
    const utilisateur = await verifierSession();
    if (!utilisateur) return;
    $('sessionUser').textContent = utilisateur.username;
    if (page === "pilotage") {
      $("appFooter").hidden = true;
      return;
    }
    await refreshPage();
    minuterieActualisation = window.setInterval(refreshPage, 10000);
  } catch (error) { showLoadError(error); }
};
demarrer();

function remplirSelect(id, items) {
  const select = $(id);
  if (!select) return;
  const signature = JSON.stringify(items.map(i => [i.id, i.nom]));
  if (select.dataset.signature === signature) return;
  const selected = select.value;
  select.innerHTML = '<option value="">Choisir…</option>' + items.map(i => `<option value="${escapeHTML(i.id)}">${escapeHTML(i.nom)}</option>`).join('');
  select.value = selected;
  select.dataset.signature = signature;
}
function badgeEtatIrrigation(etat) {
  return badge(({
    autorisee: ['off', 'Autorisée, en attente d’envoi'], commande_envoyee: ['cours', 'Commande envoyée'],
    executee: ['ok', 'Exécution confirmée'], echec: ['err', 'Échec'], non_confirmee: ['err', 'Non confirmée']
  })[etat]);
}
$('robotSelect')?.addEventListener('change', async event => {
  robotSelectionne = event.target.value;
  try { await renderPage(); } catch (error) { showLoadError(error); }
});
$('logoutButton')?.addEventListener('click', () => {
  window.deconnexionEnCours = true;
  window.clearInterval(minuterieActualisation);
  const form = document.createElement('form');
  form.method = 'POST'; form.action = '/deconnexion/';
  const csrf = document.createElement('input');
  csrf.type = 'hidden'; csrf.name = 'csrfmiddlewaretoken'; csrf.value = jetonCSRF();
  form.append(csrf); document.body.append(form); form.submit();
});
$('cultureForm')?.addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const culture = await enregistrerCulture({nom: $('cultureName').value.trim(), type_culture: $('cultureType').value.trim()});
    form.reset();
    showFormMessage(form, `Culture « ${culture.nom} » enregistrée sur le serveur.`, true);
    await refreshPage();
  } catch (error) { showFormMessage(form, error.message); } finally { libererFormulaire(form); }
});
// Bloque les doubles soumissions tout en laissant le gestionnaire métier traiter l'envoi.
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', event => {
    if (form.dataset.saving === 'true') { event.preventDefault(); event.stopImmediatePropagation(); return; }
    form.dataset.saving = 'true';
    form.querySelectorAll('[type="submit"]').forEach(button => button.disabled = true);
  }, true);
});

function libererFormulaire(form) {
  delete form.dataset.saving;
  form.querySelectorAll('[type="submit"]').forEach(button => button.disabled = false);
}
