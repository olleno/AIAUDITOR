/* Konrad OS: ditherbakgrund, klocka, Facit som skriver, räknesnurran och kapplöpningen på startsidan.
   Allt är pynt ovanpå text som redan står i HTML – utan JavaScript syns samma innehåll, bara stilla. */
(() => {
  const lugn = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Ditherbakgrund: mjuka moln i Konrads blå, rastrerade med en 4x4 Bayer-matris.
  const c = document.querySelector(".os-dither");
  if (c && c.getContext) {
    const x = c.getContext("2d");
    const B = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
    let t = 0;
    const rita = () => {
      const s = 4, w = Math.max(1, Math.ceil(c.clientWidth / s)), h = Math.max(1, Math.ceil(c.clientHeight / s));
      if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
      const farg = getComputedStyle(document.documentElement).getPropertyValue("--bla").trim() || "#1A2A9C";
      const m = /^#([0-9a-f]{6})$/i.exec(farg), r = m ? parseInt(m[1].slice(0, 2), 16) : 26,
        g = m ? parseInt(m[1].slice(2, 4), 16) : 42, b = m ? parseInt(m[1].slice(4, 6), 16) : 156;
      const img = x.createImageData(w, h), d = img.data;
      const moln = [[.16 + .03 * Math.sin(t), .12, .32], [.84, .18 + .03 * Math.cos(t * .8), .3],
        [.5 + .04 * Math.sin(t * .6), -.08, .42], [.06, .95, .28], [.96, .9, .26]];
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
        let v = 0;
        for (const q of moln) { const dx = i / w - q[0], dy = (j / h - q[1]) * 1.6; v += Math.exp(-(dx * dx + dy * dy) / (q[2] * q[2] * .35)); }
        v = Math.min(1, v * .7);
        const k = (j * w + i) * 4;
        if (v * 16 > B[j & 3][i & 3] + .5) { d[k] = r; d[k + 1] = g; d[k + 2] = b; d[k + 3] = Math.round(120 + v * 90); }
      }
      x.putImageData(img, 0, 0);
    };
    rita();
    addEventListener("resize", rita);
    if (!lugn) setInterval(() => { if (!document.hidden) { t += .05; rita(); } }, 150);
  }

  // Klockan
  const dag = ["söndag", "måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag"];
  const man = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"];
  const dEl = document.querySelector(".os-datum"), tEl = document.querySelector(".os-tid");
  if (dEl && tEl) {
    const klocka = () => {
      const n = new Date();
      dEl.textContent = `${dag[n.getDay()]} ${n.getDate()} ${man[n.getMonth()]} ${n.getFullYear()}`;
      tEl.textContent = n.toLocaleTimeString("sv-SE");
    };
    klocka(); setInterval(klocka, 1000);
  }

  // Facit skriver farfars regel
  const sk = document.querySelector(".os-skriv");
  if (sk && !lugn) {
    const regel = sk.dataset.text || sk.textContent; let i = 0;
    sk.classList.add("skriver");
    const tick = () => { sk.textContent = regel.slice(0, i++); if (i <= regel.length + 1) setTimeout(tick, 70 + Math.random() * 90); else setTimeout(() => { i = 0; tick(); }, 4000); };
    tick();
  }

  // Räknesnurrans stapel
  const st = document.querySelector(".os-stapel");
  if (st) setTimeout(() => st.classList.add("full"), 400);

  // Kapplöpningen: påhittat exempel som visar idén, ingen mätning.
  const knapp = document.getElementById("os-kor");
  if (!knapp) return;
  const tk = document.getElementById("os-tk"), td = document.getElementById("os-td"),
    sK = document.getElementById("os-sk"), sD = document.getElementById("os-sd");
  const lev = ["ICA Kvantum", "Telia", "SJ", "Clas Ohlson", "Circle K", "Restaurang Tranan", "Dustin", "Postnord", "Webhallen", "Biltema", "Fortum", "Apotea"];
  const du = ["söker \"kvitto\" i mejlen ...", "öppnar ICA Kvantum, sparar pdf", "döper om filen", "loggar in i banken",
    "letar upp beloppet 412,50 kr", "skriver in verifikatet", "räknar ut momsen", "söker \"kvitto\" igen ...", "hittar inte SJ-biljetten", "kollar skräpposten"];
  const skriv = (el, txt) => {
    const p = document.createElement("p"); p.textContent = txt; el.appendChild(p);
    while (el.scrollHeight > el.clientHeight && el.children.length > 1) el.removeChild(el.firstChild);
  };
  let igang = false;
  knapp.addEventListener("click", () => {
    if (igang) return; igang = true; knapp.disabled = true;
    tk.textContent = ""; td.textContent = "";
    skriv(tk, "$ konrad stäm-av september"); skriv(td, "$ öppna mejlen");
    let k = 0, n = 0;
    sK.textContent = "Konrad: arbetar"; sD.textContent = "Du: arbetar";
    const a = setInterval(() => {
      k++; const l = lev[k % lev.length];
      skriv(tk, [7, 19, 30].includes(k) ? `? kvitto ${k}/38 ${l}: hittar inget, frågar dig` : `✓ kvitto ${k}/38 ${l}: matchat mot banken, moms räknad`);
      if (k >= 38) { clearInterval(a); skriv(tk, "KLART. 35 matchade, 3 frågor till dig."); sK.textContent = "Konrad: klar, 3 frågor till dig"; }
    }, lugn ? 10 : 110);
    const b = setInterval(() => {
      skriv(td, "… " + du[n % du.length]); n++;
      sD.textContent = `Du: kvitto ${1 + Math.floor(n / 5)} av 38`;
      if (k >= 38 && n > 14) { clearInterval(b); skriv(td, "… klockan är 23:10. Resten nästa söndag."); igang = false; knapp.disabled = false; knapp.textContent = "Kör igen"; }
    }, lugn ? 30 : 700);
  });
})();
