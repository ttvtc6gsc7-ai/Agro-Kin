const welcomeSplash = document.getElementById("welcomeSplash");
const welcomeEnter = document.getElementById("welcomeEnter");
const reopenWelcome = document.getElementById("reopenWelcome");
const heroTitle = document.getElementById("heroTitle");

if (welcomeSplash && welcomeEnter) {
  const sessionKey = "roboAgriWelcomeSeen";
  let alreadySeen = false;

  try {
    alreadySeen = window.sessionStorage.getItem(sessionKey) === "true";
    if (!alreadySeen) window.sessionStorage.setItem(sessionKey, "true");
  } catch (error) {
    console.warn("La mémorisation du splash n’est pas disponible pour cette session.", error);
  }

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let isClosing = false;

  const finishClosing = () => {
    welcomeSplash.hidden = true;
    welcomeSplash.removeAttribute("aria-hidden");
    welcomeSplash.removeAttribute("inert");
    isClosing = false;
    if (heroTitle) heroTitle.focus({ preventScroll: true });
  };

  const closeSplash = () => {
    if (isClosing) return;
    isClosing = true;
    welcomeSplash.setAttribute("aria-hidden", "true");
    welcomeSplash.setAttribute("inert", "");
    welcomeSplash.classList.add("is-leaving");
    if (reducedMotion) {
      finishClosing();
    } else {
      window.setTimeout(finishClosing, 400);
    }
  };

  const showSplash = () => {
    isClosing = false;
    welcomeSplash.hidden = false;
    welcomeSplash.removeAttribute("aria-hidden");
    welcomeSplash.removeAttribute("inert");
    welcomeSplash.classList.remove("is-leaving");
    welcomeEnter.focus();

    const landingNav = document.getElementById("landingNav");
    const menuToggle = document.getElementById("landingMenuToggle");
    if (landingNav?.classList.contains("open")) {
      landingNav.classList.remove("open");
      menuToggle?.setAttribute("aria-expanded", "false");
      menuToggle?.setAttribute("aria-label", "Ouvrir la navigation");
    }
  };

  if (alreadySeen) {
    welcomeSplash.hidden = true;
  } else {
    showSplash();
  }

  welcomeEnter.addEventListener("click", closeSplash);
  reopenWelcome?.addEventListener("click", showSplash);
  welcomeSplash.addEventListener("keydown", event => {
    if (event.key === "Escape") closeSplash();
    if (event.key === "Tab") {
      event.preventDefault();
      welcomeEnter.focus();
    }
  });
}
