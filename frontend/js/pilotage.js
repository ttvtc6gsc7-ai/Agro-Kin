(() => {
  const directions = [...document.querySelectorAll("[data-move]")];
  const verifier = document.getElementById("verifier");
  const stop = document.getElementById("stop");
  const liaison = document.getElementById("liaison");
  const info = document.getElementById("commandeInfo");
  let actif = null;
  let arretEnCours = false;

  function activerDirections(ok) {
    directions.forEach(bouton => { bouton.disabled = !ok; });
  }

  async function envoyer(code) {
    return apiFetch("/pilotage/", {
      method: "POST", body: JSON.stringify({ move: code }), keepalive: true,
      signal: AbortSignal.timeout(3000)
    });
  }

  async function arreter() {
    if (arretEnCours) return;
    arretEnCours = true;
    const precedent = actif;
    actif = null;
    if (precedent) {
      clearTimeout(precedent.rappel);
      precedent.bouton.setAttribute("aria-pressed", "false");
    }
    info.textContent = "Demande d’arrêt en cours…";
    try {
      await envoyer("S");
      // Une direction déjà en transit peut arriver après le premier arrêt.
      if (precedent?.envoi) {
        await precedent.envoi.catch(() => {});
        await envoyer("S");
      }
      info.textContent = "Commande d’arrêt reçue par l’ESP32.";
    } catch {
      activerDirections(false);
      liaison.textContent = "Liaison à vérifier.";
      info.textContent = "Arrêt non confirmé. Vérifiez le robot sur place.";
    } finally {
      arretEnCours = false;
    }
  }

  async function maintenir(appui) {
    try {
      appui.envoi = envoyer(appui.bouton.dataset.move);
      await appui.envoi;
      appui.envoi = null;
      if (actif !== appui) return;
      info.textContent = "Commande reçue · " + appui.bouton.textContent.trim();
      appui.rappel = setTimeout(() => maintenir(appui), 250);
    } catch {
      if (actif !== appui) return;
      activerDirections(false);
      liaison.textContent = "Commande non confirmée. Vérifiez la liaison.";
      arreter();
    }
  }

  for (const bouton of directions) {
    function appuyer(source) {
      if (actif || arretEnCours || bouton.disabled) return;
      bouton.setAttribute("aria-pressed", "true");
      actif = { bouton, source };
      maintenir(actif);
    }
    function relacher(source) {
      if (actif?.bouton === bouton && actif.source === source) arreter();
    }
    bouton.addEventListener("pointerdown", event => {
      if (event.button !== 0 || actif || arretEnCours) return;
      event.preventDefault();
      bouton.setPointerCapture(event.pointerId);
      appuyer(event.pointerId);
    });
    for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) {
      bouton.addEventListener(type, event => relacher(event.pointerId));
    }
    for (const type of ["keydown", "keyup"]) {
      bouton.addEventListener(type, event => {
        if (![" ", "Enter"].includes(event.key)) return;
        event.preventDefault();
        if (type === "keyup") relacher(event.key);
        else if (!event.repeat) appuyer(event.key);
      });
    }
    bouton.addEventListener("blur", () => { if (actif?.bouton === bouton) arreter(); });
  }

  const quitter = () => { if (actif) arreter(); };
  window.addEventListener("blur", quitter);
  window.addEventListener("pagehide", quitter);
  document.addEventListener("visibilitychange", () => { if (document.hidden) quitter(); });
  stop.addEventListener("click", arreter);
  verifier.addEventListener("click", async () => {
    if (actif || arretEnCours) return;
    verifier.disabled = true;
    activerDirections(false);
    liaison.textContent = "Recherche de l’ESP32…";
    try {
      const resultat = await apiFetch("/pilotage/", { cache: "no-store", signal: AbortSignal.timeout(3500) });
      liaison.textContent = "État transmis · " + resultat.etat;
      stop.disabled = false;
      activerDirections(true);
    } catch (erreur) {
      liaison.textContent = erreur.statut === 403 ? erreur.message :
        "ESP32 injoignable. Vérifiez le réseau du poste serveur et réessayez.";
    } finally {
      verifier.disabled = false;
    }
  });
})();
