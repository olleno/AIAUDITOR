/* Priskalkylatorn på startsidan. Räkningen görs i kalkyl.js (Kalkyl.konradPris), samma kod som testerna kör. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('f') || !window.Kalkyl) return;
  const fmt = n => Math.round(n).toLocaleString('sv-SE') + ' kr';
  const tal = (id, min, max) => { let v = parseInt($(id).value, 10); if (isNaN(v)) v = min; return Math.min(max, Math.max(min, v)); };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function rakna() {
    const n = +$('niva').value, m = $('inkl').checked ? 1.25 : 1;
    const p = Kalkyl.konradPris({ niva: n, ver: tal('ver', 0, 500), bank: tal('bank', 1, 10), anst: tal('anst', 0, 50), del: tal('del', 1, 10),
      moms: $('moms').checked, gransk: $('gransk').checked, bokslut: $('bokslut').checked, privat: $('privat').checked,
      holding: $('holding').checked, byte: $('byte').checked });
    [['moms', p.momsIngar, '99 kr/mån'], ['gransk', p.granskIngar, '295 kr/mån']].forEach(([id, ing, txt]) => {
      $(id).disabled = ing; $('r-' + id).classList.toggle('av', ing); $('p-' + id).textContent = ing ? 'ingår' : txt;
    });
    const rad = (t, v, s) => `<div class="r"><span>${esc(t)}</span><span${v === 0 ? ' class="gratis"' : ''}>${v === 0 ? '0 kr' : fmt(v * m) + s}</span></div>`;
    let h = p.man.map(x => rad(x[0], x[1], '/mån')).join('');
    if (p.ar.length) h += '<div class="rub">Varje år</div>' + p.ar.map(x => rad(x[0], x[1], '/år')).join('');
    if (p.eng.length) h += '<div class="rub">En gång</div>' + p.eng.map(x => rad(x[0], x[1], '')).join('');
    $('rader').innerHTML = h;
    $('t-man').textContent = fmt(p.perManad * m) + '/mån';
    $('t-ar').textContent = fmt(p.perAr * m);
    $('t-forsta').textContent = fmt(p.forstaAret * m);
    const not = [];
    if (p.provperiod) not.push(`Bevakning är gratis de första 3 månaderna (${fmt(p.provperiod * m)} avdraget).`);
    if (!$('bokslut').checked) not.push('Utan vårt bokslutspaket behöver du köpa bokslutet någon annanstans.');
    if (n === 0 && tal('ver', 0, 500) > 15) not.push('Gratisnivån omfattar 15 verifikationer i månaden. Resten kostar 99 kr per påbörjat 25-tal.');
    not.push('Ingår inte: rådgivning utöver din nivå och revision (om ditt bolag måste ha revisor).');
    not.push(m > 1 ? 'Priser med moms.' : 'Priser utan moms.');
    $('not').textContent = not.join(' ');
  }
  ['input', 'change'].forEach(ev => $('f').addEventListener(ev, rakna));
  $('inkl').addEventListener('change', rakna);
  $('f').addEventListener('submit', e => e.preventDefault());
  rakna();
})();
