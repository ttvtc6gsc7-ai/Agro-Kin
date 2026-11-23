// Menu déroulant de la page d'accueil sur les écrans étroits.
const menuToggle = document.getElementById("landingMenuToggle");
const landingNav = document.getElementById("landingNav");

menuToggle?.addEventListener("click", () => {
  const isOpen = landingNav.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Fermer la navigation" : "Ouvrir la navigation");
});

landingNav?.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener("click", () => {
    landingNav.classList.remove("open");
    menuToggle?.setAttribute("aria-expanded", "false");
    menuToggle?.setAttribute("aria-label", "Ouvrir la navigation");
  });
});

// Année du pied de page calculée automatiquement.
document.getElementById("currentYear").textContent = new Date().getFullYear();

// Révèle les sections lorsqu'elles entrent dans la fenêtre, sans dépendance d'animation externe.
const revealItems = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      revealObserver.unobserve(entry.target);
    });
  }, { threshold: 0.14 });
  revealItems.forEach(item => revealObserver.observe(item));
} else {
  revealItems.forEach(item => item.classList.add("is-visible"));
}

// Messages informatifs alternés dans le bandeau de présentation.
const heroMessage = document.getElementById("heroMessage");
const heroHeadlineMessage = document.getElementById("heroHeadlineMessage");
const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
if (heroMessage && !motionPreference.matches) {
  const headlines = [
    heroHeadlineMessage?.textContent || "Et si la technologie prenait soin de vos cultures\u00a0?",
    "Un suivi attentif pour chaque parcelle.",
    "Mieux comprendre l’humidité de vos sols.",
    "Une irrigation suivie avec précision."
  ];
  const messages = [
    heroMessage.textContent,
    "Consultez les mesures d’humidité, les missions et les événements observés pour comprendre l’évolution de chaque parcelle.",
    "RoboAgri-Kin rassemble les informations de supervision afin de faciliter le suivi des besoins en eau des cultures.",
    "Cette démonstration universitaire utilise des données simulées pour illustrer le suivi des parcelles, des missions et de l’irrigation."
  ];
  let messageIndex = 0;
  let fadeTimer;
  const messageTimer = window.setInterval(() => {
    if (document.visibilityState !== "visible") return;
    heroMessage.classList.add("is-changing");
    heroHeadlineMessage?.classList.add("is-changing");
    fadeTimer = window.setTimeout(() => {
      messageIndex = (messageIndex + 1) % messages.length;
      heroMessage.textContent = messages[messageIndex];
      if (heroHeadlineMessage) heroHeadlineMessage.textContent = headlines[messageIndex];
      heroMessage.classList.remove("is-changing");
      heroHeadlineMessage?.classList.remove("is-changing");
    }, 550);
  }, 7000);

  const stopMessagesForReducedMotion = event => {
    if (!event.matches) return;
    window.clearInterval(messageTimer);
    window.clearTimeout(fadeTimer);
    heroMessage.classList.remove("is-changing");
    heroHeadlineMessage?.classList.remove("is-changing");
  };
  if (motionPreference.addEventListener) {
    motionPreference.addEventListener("change", stopMessagesForReducedMotion);
  } else {
    motionPreference.addListener(stopMessagesForReducedMotion);
  }
}
