/* 3:12-kalkylatorn. Reglerna läses ur data-regler-312-2026 (data/regler-312-2026.json), räkningen görs i kalkyl.js. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('tolv') || !window.Kalkyl) return;
  const R = JSON.parse($('data-regler-312-2026').textContent);
  const fmt = n => Math.round(n).toLocaleString('sv-SE') + ' kr';
  const num = id => { const v = parseFloat(String($(id).value).replace(',', '.')); return isNaN(v) ? 0 : v; };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function rakna() {
    const r = Kalkyl.tolv({ agdeVidArsskiftet: $('agde').checked, andelProcent: num('andel'), loneunderlag: num('lu'), egenLon: num('egen'),
      omkostnadsbelopp: num('omk'), sparat: num('sparat'), utdelning: num('utd') }, R);
    if (!r.ok) {
      $('u-grans').textContent = '–'; $('u-text').textContent = '';
      $('u-rader').innerHTML = ''; $('u-not').innerHTML = r.fel.map(f => `<p class="varning">${esc(f)}</p>`).join('');
      return;
    }
    $('u-grans').textContent = fmt(r.gransbelopp);
    $('u-text').textContent = `Ditt gränsbelopp för 2026. Utdelning upp till det beloppet beskattas med 20 %.`;
    const rad = (t, v, k) => `<div class="r${k ? ' ' + k : ''}"><span>${esc(t)}</span><span>${v}</span></div>`;
    $('u-rader').innerHTML =
      rad(`Grundbelopp (${fmt(r.grundbeloppHela)} × din andel)`, fmt(r.grundbelopp)) +
      rad(`Lönebaserat utrymme (50 % av ${fmt(r.andelAvUnderlag)} − ${fmt(r.loneavdrag)})`, fmt(r.lonebaserat)) +
      rad(`Ränta på omkostnadsbelopp över 100 000 kr (${(r.rantesats * 100).toFixed(2).replace('.', ',')} %)`, fmt(r.ranta)) +
      rad('Sparat utdelningsutrymme', fmt(r.sparat)) +
      rad('Gränsbelopp 2026', fmt(r.gransbelopp), 'sum') +
      rad('Utdelning inom gränsbeloppet', fmt(r.inom)) +
      rad('Skatt på den (20 %)', fmt(r.skattInom)) +
      rad('Kvar efter skatt', fmt(r.nettoInom)) +
      (r.over ? rad('Utdelning över gränsbeloppet (beskattas som lön)', fmt(r.over)) : '') +
      rad('Sparas till 2027 (utan uppräkning)', fmt(r.sparatTillNasta));
    $('u-not').innerHTML = r.not.map(f => `<p class="varning">${esc(f)}</p>`).join('') +
      `<p class="liten">Regler kontrollerade ${esc(R.kontrollerad)} mot Skatteverket. Uppskattning, inte ett personligt råd.</p>`;
  }
  ['input', 'change'].forEach(ev => $('tolv').addEventListener(ev, rakna));
  $('tolv').addEventListener('submit', e => e.preventDefault());
  rakna();
})();
