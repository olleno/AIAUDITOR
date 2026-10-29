/* "Vad kostar din bokföring i dag och hos Konrad". Räkningen görs i kalkyl.js (Kalkyl.jamfor). */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('jmf') || !window.Kalkyl) return;
  const fmt = n => Math.round(n).toLocaleString('sv-SE') + ' kr';
  const num = id => { const v = parseFloat($(id).value); return isNaN(v) || v < 0 ? 0 : v; };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function rakna() {
    const r = Kalkyl.jamfor({ typ: $('typ').value, byraManad: num('byra'), programManad: num('prog'), bokslutAr: num('bok'),
      ver: num('ver2'), bank: 1, anst: num('anst2'), del: 1 });
    $('j-rub').textContent = r.billigare ? `Hos Konrad (${r.nivanamn}) betalar du per år` : `Konrad (${r.nivanamn}) blir dyrare per år`;
    $('j-skillnad').textContent = (r.billigare ? fmt(r.skillnad) + ' mindre' : fmt(-r.skillnad) + ' mer');
    $('j-text').textContent = r.forklaring;
    const rad = (t, v, k) => `<div class="r${k ? ' ' + k : ''}"><span>${esc(t)}</span><span>${v}</span></div>`;
    $('j-rader').innerHTML = rad('Du betalar i dag, per år', fmt(r.idag)) +
      r.konrad.man.filter(x => x[1]).map(x => rad(`${x[0]} × 12`, fmt(x[1] * 12))).join('') +
      r.konrad.ar.map(x => rad(x[0], fmt(x[1]))).join('') +
      rad(`Konrad per år`, fmt(r.konradAr), 'sum') +
      (r.konrad.provperiod ? rad('Första året, med 3 månader gratis Bevakning', fmt(r.konrad.forstaAret)) : '') +
      '<p class="liten">Alla belopp exkl. moms. Flytt från gammal byrå 1 495 kr en gång ingår inte.</p>';
  }
  ['input', 'change'].forEach(ev => $('jmf').addEventListener(ev, rakna));
  $('jmf').addEventListener('submit', e => e.preventDefault());
  rakna();
})();
