const search = document.querySelector('#search');
const chapters = [...document.querySelectorAll('[data-chapter]')];
const links = [...document.querySelectorAll('nav a')];
const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const texts = chapters.map(el => normalize(el.textContent));
search.addEventListener('input', () => {
  const query = normalize(search.value.trim());
  let count = 0;
  chapters.forEach((el, i) => {
    const match = texts[i].includes(query);
    el.hidden = !match;
    links[i].hidden = !match;
    if (match) count++;
  });
  document.querySelector('#search-status').textContent = query ? `${count} chapitre(s) trouvé(s)` : '';
  document.querySelector('#empty').hidden = count > 0;
});
function revealHash() {
  const id = decodeURIComponent(location.hash.slice(1));
  const target = document.getElementById(id);
  if (!target) return;
  let parent = target;
  while (parent) {
    if (parent.tagName === 'DETAILS') parent.open = true;
    parent.hidden = false;
    parent = parent.parentElement;
  }
  requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
}
window.addEventListener('hashchange', revealHash);
if (location.hash) revealHash();
const observer = new IntersectionObserver(entries => {
  for (const entry of entries) if (entry.isIntersecting) {
    links.forEach(link => {
      const active = link.hash === `#${entry.target.id}`;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
}, {rootMargin: '0px 0px -70% 0px'});
chapters.forEach(el => observer.observe(el));
const fields = ['min', 'max', 'value', 'threshold'].map(name => document.querySelector(`#sim-${name}`));
function calculate() {
  const [min, max, value, threshold] = fields.map(el => Number(el.value));
  const result = document.querySelector('#sim-result');
  if (fields.some(el => el.value === '') || ![min,max,value,threshold].every(Number.isFinite) || max <= min) {
    result.textContent = 'Saisir quatre nombres valides, avec maximum strictement supérieur au minimum.';
    return;
  }
  if (value < min || value > max) {
    result.textContent = 'Mesure invalide : la valeur brute est hors de la plage d’étalonnage. Aucune recommandation.';
    return;
  }
  const humidity = Math.round((value-min)*100/(max-min)*100)/100;
  result.textContent = `${humidity.toLocaleString('fr-FR', {minimumFractionDigits:2,maximumFractionDigits:2})} % — ${humidity < threshold ? 'recommandation d’irrigation, sous réserve d’un seuil actif et d’une autorisation humaine.' : 'aucune recommandation : humidité supérieure ou égale au minimum.'}`;
}
fields.forEach(el => el.addEventListener('input', calculate));
calculate();
let printState = [];
window.addEventListener('beforeprint', () => {
  printState = [...document.querySelectorAll('details')].map(el => [el,el.open]);
  printState.forEach(([el]) => el.open = true);
});
window.addEventListener('afterprint', () => printState.forEach(([el,open]) => el.open = open));
document.querySelector('#print').addEventListener('click', () => window.print());
