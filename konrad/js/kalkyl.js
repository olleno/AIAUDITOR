/* Konrads räknefunktioner. Rena funktioner utan sidkod, så att samma kod körs i webbläsaren och i testerna
   (tester/kalkyl.test.js). Priserna kommer från data/konrad-priser.json, 3:12-reglerna från
   data/regler-312-2026.json. Båda läggs in i sidan av build.py.

   3:12 inkomstår 2026, källa: Skatteverket, "Ändrade regler för delägare i fåmansföretag inför
   inkomstdeklarationen 2027", kontrollerad 2026-10-20:
   https://www.skatteverket.se/foretag/drivaforetag/foretagsformer/famansforetag/andradereglerinforinkomstdeklarationen2027.4.4a54dc8b19aa6175a152359.html
*/
(function (root) {
  'use strict';

  const avrunda = n => Math.round(n);

  /* ---------- Konrads pris ---------- */
  // niva: 0 Gratis, 1 Bevakning, 2 Pro, 3 Kamrer, 4 Ekonomichef
  const NIVAPRIS = [0, 199, 399, 2995, 4995];
  const NIVANAMN = ['Gratis', 'Bevakning', 'Pro', 'Kamrer', 'Ekonomichef'];

  function konradPris(o) {
    const n = o.niva | 0;
    const ver = Math.max(0, o.ver | 0), bank = Math.max(1, o.bank | 0), anst = Math.max(0, o.anst | 0), del = Math.max(1, o.del | 0);
    const momsIngar = n >= 1, granskIngar = n >= 3, volymIngar = n >= 3;
    const man = [['Löpande bokföring', 0]];
    if (n) man.push([NIVANAMN[n], NIVAPRIS[n]]);
    const blk = volymIngar ? 0 : Math.ceil(Math.max(0, ver - 15) / 25);
    if (blk) man.push([`Fler verifikationer (${blk} × 25)`, blk * 99]);
    if (bank > 1) man.push([`Extra bankkonton (${bank - 1})`, (bank - 1) * 49]);
    if (anst) man.push([`Lön (${anst} anställda)`, anst * 195]);
    if (!momsIngar && o.moms) man.push(['Momsen inlämnad åt dig', 99]);
    if (!granskIngar && o.gransk) man.push(['Granskad bokföring', 295]);
    const ar = [];
    if (o.bokslut !== false) ar.push(['Bokslut och årsredovisning', 5995]);
    if (del > 1) ar.push([`K10 för fler delägare (${del - 1})`, (del - 1) * 495]);
    if (o.privat) ar.push(['Din privata deklaration', 1495]);
    if (o.holding) ar.push(['Holdingbolag', 3995]);
    const eng = o.byte ? [['Flytt från gammal byrå', 1495]] : [];
    const sum = a => a.reduce((s, x) => s + x[1], 0);
    const perManad = sum(man);
    const provperiod = n === 1 ? 3 * 199 : 0;
    const perAr = perManad * 12 + sum(ar);
    return { man, ar, eng, perManad, perAr, provperiod, forstaAret: perAr + sum(eng) - provperiod, momsIngar, granskIngar };
  }

  /* ---------- Vad kostar din bokföring i dag och hos Konrad ---------- */
  // typ: 'sjalv'  = du bokför själv i ett program, byrån (eller du) gör bokslutet
  //      'bokfor' = byrån bokför åt dig
  //      'rad'    = byrån bokför, granskar varje månad och ger råd löpande
  function jamfor(o) {
    const idag = (+o.byraManad || 0) * 12 + (+o.programManad || 0) * 12 + (+o.bokslutAr || 0);
    const niva = o.typ === 'rad' ? 3 : o.typ === 'bokfor' ? 1 : 0;
    const konrad = konradPris({
      niva, ver: o.ver, bank: o.bank, anst: o.anst, del: o.del,
      moms: false, gransk: o.typ === 'bokfor', bokslut: true,
    });
    const skillnad = idag - konrad.perAr; // positivt = Konrad billigare
    let forklaring;
    if (o.typ === 'rad') forklaring = 'Din byrå granskar och ger råd varje månad. Det motsvarar Kamrer hos Konrad, där en auktoriserad redovisningskonsult gör samma sak.';
    else if (o.typ === 'bokfor') forklaring = 'Din byrå bokför åt dig. Hos Konrad motsvarar det Bevakning, där Konrad bokför och lämnar in momsen, plus granskad bokföring av en människa varje månad.';
    else forklaring = 'Du bokför själv. Hos Konrad räcker Gratis, där Konrad bokför det han är säker på och frågar om resten, plus bokslutet.';
    return { idag: avrunda(idag), niva, nivanamn: NIVANAMN[niva], konrad, konradAr: konrad.perAr, skillnad: avrunda(skillnad), billigare: skillnad > 0, forklaring };
  }

  /* ---------- 3:12-kedjan, inkomstår 2026 ---------- */
  function tolv(i, R) {
    const fel = [];
    const andel = Math.min(100, Math.max(0, +i.andelProcent || 0)) / 100;
    if (!i.agdeVidArsskiftet) {
      return { ok: false, fel: ['Du måste ha ägt aktierna vid ingången av 2026 för att få ett gränsbelopp för 2026. Kalkylatorn räknar inte vidare. Kontrollera med Skatteverket.'] };
    }
    if (andel <= 0) return { ok: false, fel: ['Fyll i hur stor del av bolaget du äger.'] };
    const ibb = R.ibb_aret_fore;
    const grundbeloppHela = R.grundbelopp_antal_ibb * ibb;           // 322 400 kr
    const grundbelopp = grundbeloppHela * andel;
    const loneavdrag = R.loneavdrag_antal_ibb * ibb;                   // 644 800 kr
    const loneunderlag = Math.max(0, +i.loneunderlag || 0);
    const andelAvUnderlag = loneunderlag * andel;
    const lonebaseratFore = R.lonebaserat_andel * Math.max(0, andelAvUnderlag - loneavdrag);
    const tak = R.lonebaserat_tak_ganger_egen_lon * Math.max(0, +i.egenLon || 0);
    const lonebaserat = Math.min(lonebaseratFore, tak);
    const rantesats = R.statslanerante_30_nov_aret_fore + R.ranta_paslag; // 11,55 %
    const omk = Math.max(0, +i.omkostnadsbelopp || 0);
    const ranta = Math.max(0, omk - R.rantefri_del_omkostnadsbelopp) * rantesats;
    const sparat = Math.max(0, +i.sparat || 0);
    const gransbelopp = grundbelopp + lonebaserat + ranta + sparat;
    const utdelning = Math.max(0, +i.utdelning || 0);
    const inom = Math.min(utdelning, gransbelopp);
    const over = Math.max(0, utdelning - gransbelopp);
    const skattInom = inom * R.skatt_inom_gransbelopp;
    const sparatTillNasta = gransbelopp - inom; // räknas inte upp med ränta (nya regler)
    const not = [];
    if (lonebaseratFore > tak) not.push(`Det lönebaserade utrymmet begränsas till 50 gånger din eller en närståendes kontanta lön från bolaget (${avrunda(tak).toLocaleString('sv-SE')} kr).`);
    if (andelAvUnderlag > 0 && andelAvUnderlag <= loneavdrag) not.push('Din del av löneunderlaget är lägre än löneavdraget på 8 inkomstbasbelopp, så det lönebaserade utrymmet blir 0 kr.');
    if (over > 0) not.push(`${avrunda(over).toLocaleString('sv-SE')} kr av utdelningen ligger över gränsbeloppet. Den delen beskattas som inkomst av tjänst, alltså med din vanliga inkomstskatt. Kalkylatorn räknar inte ut den skatten.`);
    return {
      ok: true, fel,
      grundbeloppHela: avrunda(grundbeloppHela), grundbelopp: avrunda(grundbelopp),
      loneavdrag: avrunda(loneavdrag), andelAvUnderlag: avrunda(andelAvUnderlag),
      lonebaseratFore: avrunda(lonebaseratFore), tak: avrunda(tak), lonebaserat: avrunda(lonebaserat),
      rantesats, ranta: avrunda(ranta), sparat: avrunda(sparat), gransbelopp: avrunda(gransbelopp),
      utdelning: avrunda(utdelning), inom: avrunda(inom), over: avrunda(over), skattInom: avrunda(skattInom),
      nettoInom: avrunda(inom - skattInom), sparatTillNasta: avrunda(sparatTillNasta), not,
    };
  }

  /* ---------- Försvunna kvitton (kampanjen "Jakten på det försvunna kvittot") ----------
     Räkneexempel, inget besked om vad Skatteverket beslutar i ett enskilt fall.
     Momsen: utan faktura (kvitto) kan avdraget för ingående moms nekas. Skatteverket, "Momslagens regler om
     fakturering", kontrollerad 2026-10-21. Momssatserna 25, 12 och 6 %: Skatteverket, "Momssats på varor och
     tjänster", kontrollerad 2026-10-21. Bolagsskatt 20,6 %: Skatteverket, "Aktiebolag", kontrollerad 2026-10-21.
     Beloppet per kvitto är inklusive moms. Momsen i beloppet = belopp × sats / (1 + sats).
     Om också kostnadsavdraget nekas blir vinsten högre med beloppet utan moms, och bolagsskatten ökar med
     20,6 % av det (värsta fallet, för ett aktiebolag med vinst). */
  const BOLAGSSKATT = 0.206;
  const MOMSSATSER = [0.25, 0.12, 0.06];

  function kvitton(o) {
    const belopp = Math.max(0, +o.belopp || 0);
    const antal = Math.max(0, Math.floor(+o.antal || 0));
    const sats = MOMSSATSER.includes(+o.momssats) ? +o.momssats : 0.25;
    const summa = belopp * antal;
    const moms = summa * sats / (1 + sats);
    const exkl = summa - moms;
    const skatt = o.nekasKostnad ? exkl * BOLAGSSKATT : 0;
    return { summa: avrunda(summa), moms: avrunda(moms), exkl: avrunda(exkl), skatt: avrunda(skatt),
      totalt: avrunda(moms + skatt), sats, nekasKostnad: !!o.nekasKostnad };
  }

  const api = { konradPris, jamfor, tolv, kvitton, NIVAPRIS, NIVANAMN, BOLAGSSKATT, MOMSSATSER };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Kalkyl = api;
})(typeof window !== 'undefined' ? window : globalThis);
