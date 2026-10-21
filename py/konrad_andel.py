"""Så mycket hade Konrad bokfört själv – en ärlig, regelbaserad uppskattning ur SIE-filen.

Körs i webbläsaren (Pyodide) som resten av granskningen. Filen lämnar aldrig datorn.
Visas BARA i gratisversionen på aiauditor.se (rapport.bygg(..., variant="gratis")).
Byråversionen nämner aldrig Konrad (Olles beslut 20 okt 2026).

Reglerna (exakt det koden gör; testerna i tester/aiauditor_test_konrad_andel.py är facit):

Varje verifikation med minst en rad bedöms. Tomma verifikationer räknas inte.
Verifikationens belopp = summan av raderna i debet (positiva belopp).
Kontonummer läses som heltal (de fyra första siffrorna).

Skäl att gå till en människa (en verifikation kan ha flera):
  STORT       belopp över 25 000 kr (Konrads gräns för automatisk bokföring) – men bara för NYA och OVANLIGA poster
              (Olles beslut 21 okt 2026). Gränsen gäller INTE (verifikationen får då undantaget i "undantag"):
                LON         lön: minst en rad på 7000–7399 (löner) och minst en på 2710–2739 (personalskatt eller
                            arbetsgivaravgifter), och alla rader på 7000–7699, 2710–2739 eller 1900–1999.
                KUNDBET     kundbetalning som matchar en egen faktura: alla rader på 1510 (kredit) eller 1900–1999, och
                            en annan verifikation med samma datum eller tidigare har 1510 i debet på exakt samma belopp
                            (kundfordran). Varje kundfordran matchar högst en betalning. (I en SIE-fil syns inte OCR eller
                            referens – Konrad kräver dem i drift; här räcker kundfordran med samma belopp.)
                ATERKOMMANDE samma text och samma kontouppsättning (som ATERKOMMER nedan) finns i minst 2 verifikationer
                            TIDIGARE i filen (datum, sedan ordningen i filen). I filen syns inte vem som godkänt något;
                            de två första gångerna räknas som de som en människa har godkänt.
              De andra skälen gäller som vanligt för de här verifikationerna.
  REPR        någon rad på 6070–6079 (representation).
  INVEST      någon rad i debet på 1000–1299 (köp av anläggningstillgång).
  AGARE       någon rad på 1680–1689 eller 2890–2899 (ägare eller närstående).
  BOKSLUT     någon rad på 1700–1799, 2000–2099, 2650, 2900–2999 eller 8800–8999
              (periodisering, eget kapital, momsredovisning, bokslut eller skatt).
  SARMOMS     någon rad på 2614–2618, 2624–2628, 2634–2638 eller 2645–2649
              (omvänd skattskyldighet, köp från utlandet och liknande).
  MOMS        momsen stämmer inte med 25, 12 eller 6 %:
                - ingående moms = summan av debet på 2640–2641. Om den är > 0:
                  underlag = summan av debet på 1000–1299 och 4000–7999.
                  Stämmer om underlaget > 0 och ingående moms ligger inom 1 kr
                  från underlaget × 25 %, 12 % eller 6 %.
                - utgående moms = summan av kredit på 2610–2613 (25 %), 2620–2623 (12 %)
                  och 2630–2633 (6 %). Har mer än en av grupperna kredit stämmer det inte.
                  Har exakt en grupp kredit: underlag = summan av kredit på 3000–3999,
                  och momsen ska ligga inom 1 kr från underlaget × gruppens sats.
  RATTELSE    någon rad i kredit på 4000–7999 eller i debet på 3000–3999
              (rättelse, kreditnota eller omföring).
  SALLAN      något konto används i högst 2 verifikationer i filen. Avräkningskonton
              räknas inte: 1500–1599, 1630, 1900–1999, 2400–2499, 2600–2699, 2700–2799.
  FYND        granskningen har ett fynd på just den verifikationen (oavsett allvar).
  MONSTER     inget av skälen ovan, men verifikationen passar inget känt mönster (se nedan). Ett undantag från
              25 000-gränsen (LON, KUNDBET, ATERKOMMANDE) räknas också som ett känt mönster.

Kända mönster (minst ett krävs för "automatiskt"):
  ATERKOMMER  samma text och samma kontouppsättning förekommer i minst 3 verifikationer i filen.
              Text jämförs i små bokstäver, där allt som inte är bokstäver blir mellanslag
              ("Faktura 1001 konsultuppdrag" och "Faktura 1002 konsultuppdrag" är samma).
              Månadsnamn och deras förkortningar (januari, jan, feb ...) tas bort, så att
              "Lön januari" och "Lön februari" är samma.
  BANK        verifikationen har en rad på 1900–1999 och en tydlig text: texten är inte tom
              och inte bara ett allmänt ord (se ALLMANNA).

Automatiskt = inget skäl att gå till en människa.

Tidsbesparing (uppskattning): timmar = antal automatiska × minuter per verifikation / 60.
Kronor = timmar × kundens eget timpris, avrundat till hela kronor.
Standardvärdet 5 minuter är ett antagande: Exsitec räknar med 5 minuter per faktura i sitt
räkneexempel (exsitec.se/artiklar/ga-fran-55-till-80-automatisk-hantering, hämtad 2026-10-21).
"""
import math, re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from collections import Counter

GRANS = 25000.0
STANDARD_MINUTER = 5
KALLA_MINUTER = ("Antagande. Exsitec räknar med 5 minuter per faktura i sitt räkneexempel "
                 "(exsitec.se/artiklar/ga-fran-55-till-80-automatisk-hantering, hämtad 2026-10-21).")

SKAL = {  # ordning = visningsordning vid lika antal
    "STORT": "Ny eller ovanlig post över 25 000 kr (Konrads gräns)",
    "FYND": "Granskningen har en anmärkning på verifikationen",
    "MOMS": "Momsen stämmer inte med 25, 12 eller 6 %",
    "REPR": "Representation",
    "INVEST": "Köp av inventarier eller annan anläggningstillgång",
    "AGARE": "Ägare eller närstående",
    "BOKSLUT": "Bokslut, periodisering, momsredovisning eller skatt",
    "SARMOMS": "Omvänd moms eller köp från utlandet",
    "RATTELSE": "Rättelse, kreditnota eller omföring",
    "SALLAN": "Konto som används högst två gånger på året",
    "MONSTER": "Inget känt mönster (varken återkommande eller bankrad med tydlig text)",
}
ALLMANNA = {"betalning", "inbetalning", "utbetalning", "överföring", "insättning", "uttag", "bank",
            "swish", "kort", "kortköp", "diverse", "övrigt", "okänd", "okänt", "verifikation", "ver"}
AVRAKNING = ((1500, 1599), (1630, 1630), (1900, 1999), (2400, 2499), (2600, 2699), (2700, 2799))
MOMS_UTG = ((2610, 2613, 0.25), (2620, 2623, 0.12), (2630, 2633, 0.06))
SATSER = (0.25, 0.12, 0.06)
UNDANTAG = {  # Olles beslut 21 okt 2026: 25 000-gränsen gäller bara nya och ovanliga poster
    "LON": "Lön",
    "KUNDBET": "Kundbetalning mot en egen faktura",
    "ATERKOMMANDE": "Återkommande post som en människa redan godkänt två gånger",
}


def _nr(konto):
    m = re.match(r"\d{4}", str(konto).strip())
    return int(m.group()) if m else -1


def _i(k, *spann):
    return any(a <= k <= b for a, b in spann)


MANADER = {"januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november",
           "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "okt", "nov", "dec"}


def normtext(t):
    return " ".join(w for w in "".join(c if c.isalpha() else " " for c in (t or "").lower()).split() if w not in MANADER)


def _ref(v):
    s = str(v["serie"])
    return f"{s}{v['nr']}" if not s[-1:].isdigit() else f"{s}:{v['nr']}"


def _moms_ok(rader):
    """None = ingen moms att kontrollera, True = stämmer, False = stämmer inte."""
    kontroll = None
    ing = sum(b for k, b in rader if _i(k, (2640, 2641)) and b > 0)
    if ing > 0.005:
        und = sum(b for k, b in rader if _i(k, (1000, 1299), (4000, 7999)) and b > 0)
        kontroll = und > 0.005 and any(abs(ing - und * s) <= 1.0 for s in SATSER)
    grupper = [(sum(-b for k, b in rader if a <= k <= z and b < 0), s) for a, z, s in MOMS_UTG]
    grupper = [(m, s) for m, s in grupper if m > 0.005]
    if grupper:
        if len(grupper) > 1:
            ok = False
        else:
            m, s = grupper[0]
            und = sum(-b for k, b in rader if _i(k, (3000, 3999)) and b < 0)
            ok = und > 0.005 and abs(m - und * s) <= 1.0
        kontroll = ok if kontroll is None else (kontroll and ok)
    return kontroll


def berakna(bok, fynd=()):
    """Delar in verifikationerna i automatiskt / människa. Returnerar en ordbok (se testerna)."""
    ver = [v for v in bok["ver"] if v["rader"]]
    rader = {id(v): [(_nr(k), float(b)) for k, b in v["rader"]] for v in ver}
    anv = Counter()
    for v in ver:
        for k in {k for k, _ in rader[id(v)]}:
            anv[k] += 1
    monster = Counter((normtext(v["text"]), frozenset(k for k, _ in rader[id(v)])) for v in ver)
    flaggade = {f["ver"] for f in fynd if f.get("ver") not in (None, "", "–")}

    # Olles beslut 21 okt 2026: 25 000-gränsen gäller bara nya och ovanliga poster.
    ordnade = sorted(range(len(ver)), key=lambda i: (ver[i]["datum"] or date.min, i))
    tidigare, sett = {}, Counter()
    for i in ordnade:
        nyckel = (normtext(ver[i]["text"]), frozenset(k for k, _ in rader[id(ver[i])]))
        tidigare[id(ver[i])] = sett[nyckel]
        sett[nyckel] += 1
    kundfordringar = [(ver[i]["datum"] or date.min, i, round(b, 2)) for i in ordnade
                      for k, b in rader[id(ver[i])] if k == 1510 and b > 0]
    anvanda = set()

    def undantag(v, r):
        if (any(_i(k, (7000, 7399)) for k, _ in r) and any(_i(k, (2710, 2739)) for k, _ in r)
                and all(_i(k, (7000, 7699), (2710, 2739), (1900, 1999)) for k, _ in r)):
            return "LON"
        betalt = round(-sum(b for k, b in r if k == 1510), 2)
        if (betalt > 0 and all(k == 1510 or _i(k, (1900, 1999)) for k, _ in r)
                and all(b < 0 for k, b in r if k == 1510)):
            for d, i, b in kundfordringar:
                if ver[i] is not v and (d, i) not in anvanda and b == betalt and d <= (v["datum"] or date.min):
                    anvanda.add((d, i))
                    return "KUNDBET"
        if tidigare[id(v)] >= 2:
            return "ATERKOMMANDE"
        return None

    resultat = []
    for nr in ordnade:
        v = ver[nr]
        r = rader[id(v)]
        skal = []
        belopp = sum(b for _, b in r if b > 0)
        und = undantag(v, r) if belopp > GRANS + 0.005 else None
        if belopp > GRANS + 0.005 and not und: skal.append("STORT")
        if _ref(v) in flaggade: skal.append("FYND")
        if _moms_ok(r) is False: skal.append("MOMS")
        if any(_i(k, (6070, 6079)) for k, _ in r): skal.append("REPR")
        if any(_i(k, (1000, 1299)) and b > 0 for k, b in r): skal.append("INVEST")
        if any(_i(k, (1680, 1689), (2890, 2899)) for k, _ in r): skal.append("AGARE")
        if any(_i(k, (1700, 1799), (2000, 2099), (2650, 2650), (2900, 2999), (8800, 8999)) for k, _ in r): skal.append("BOKSLUT")
        if any(_i(k, (2614, 2618), (2624, 2628), (2634, 2638), (2645, 2649)) for k, _ in r): skal.append("SARMOMS")
        if any((_i(k, (4000, 7999)) and b < 0) or (_i(k, (3000, 3999)) and b > 0) for k, b in r): skal.append("RATTELSE")
        if any(anv[k] <= 2 and not _i(k, *AVRAKNING) for k, _ in r): skal.append("SALLAN")
        nt = normtext(v["text"])
        aterkommer = monster[(nt, frozenset(k for k, _ in r))] >= 3
        bank = any(_i(k, (1900, 1999)) for k, _ in r) and nt != "" and nt not in ALLMANNA
        if not skal and not (aterkommer or bank or und): skal.append("MONSTER")  # ett undantag är också ett känt mönster
        resultat.append({"ver": _ref(v), "belopp": round(belopp, 2), "auto": not skal, "skal": skal,
                         "monster": [m for m, j in (("ATERKOMMER", aterkommer), ("BANK", bank)) if j],
                         "undantag": und, "_i": nr})
    resultat.sort(key=lambda x: x.pop("_i"))

    totalt = len(resultat)
    auto = sum(1 for x in resultat if x["auto"])
    per_skal = Counter(s for x in resultat for s in x["skal"])
    ordning = list(SKAL)
    skal_lista = sorted(per_skal.items(), key=lambda kv: (-kv[1], ordning.index(kv[0])))
    exempel = {s: [x["ver"] for x in resultat if s in x["skal"]][:3] for s in per_skal}
    return {"totalt": totalt, "auto": auto, "manniska": totalt - auto,
            "andel_auto": (auto / totalt) if totalt else 0.0,
            "skal": [{"id": s, "text": SKAL[s], "antal": n, "exempel": exempel[s]} for s, n in skal_lista],
            "undantag": {u: sum(1 for x in resultat if x["undantag"] == u) for u in UNDANTAG},
            "verifikationer": resultat}


def tid(auto, minuter=STANDARD_MINUTER, timpris=None):
    """Uppskattad tidsbesparing. Samma formel som i webbläsaren (index.html, konradRakna)."""
    timmar = auto * minuter / 60.0
    kronor = math.floor(timmar * timpris + 0.5) if timpris else None  # som Math.round i JS
    return {"timmar": timmar, "kronor": kronor}


# ---------- HTML (bara gratisversionen) ----------
def _kr(x):
    return f"{x:,.0f}".replace(",", " ")


def _dec(x, d=1):
    """Avrundar som webbläsarens toLocaleString (halva uppåt på det exakta värdet)."""
    v = Decimal(x).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def _pct(x):
    return _dec(x * 100, 0) + " %"


def html(res, e):
    """Avsnittet "Så mycket hade Konrad bokfört själv". e = html.escape."""
    if not res["totalt"]:
        return ""
    t = tid(res["auto"])
    skalrader = "".join(
        f'<li><b>{n["antal"]}</b> {e(n["text"])} <span class="dim">(t.ex. {e(", ".join(n["exempel"]))})</span></li>'
        for n in res["skal"][:6])
    return (
        f'<div class="konrad" id="konrad-andel" data-auto="{res["auto"]}">'
        '<p class="etikett">Uppskattning · inget löfte</p>'
        '<h2>Så mycket hade Konrad bokfört själv</h2>'
        '<p class="sub">Konrad är vår systertjänst som sköter bokföringen åt dig. Vi har gått igenom verifikationerna i din fil med fasta regler '
        'och räknat hur många som liknar det Konrad bokför utan att en människa behöver titta.</p>'
        '<div class="kort">'
        f'<div class="k"><b style="color:#1A2A9C">{res["auto"]} av {res["totalt"]}</b>hade gått automatiskt ({_pct(res["andel_auto"])})</div>'
        f'<div class="k"><b>{res["manniska"]}</b>hade behövt en människa ({_pct(1 - res["andel_auto"])})</div></div>'
        '<h3>Därför hade en människa behövt titta</h3>'
        f'<ul class="skal">{skalrader}</ul>'
        '<p class="dim">En verifikation kan ha flera skäl, så siffrorna kan bli fler än antalet verifikationer.</p>'
        '<details class="regler"><summary>Så räknar vi (reglerna)</summary>'
        '<p><b>Automatiskt</b> räknas en verifikation som inte har något av skälen ovan och som antingen återkommer '
        '(samma text och samma konton minst 3 gånger i filen) eller är en bankrad med tydlig text.</p>'
        '<p><b>Till en människa</b> går nya och ovanliga poster över 25 000 kr (Konrads gräns), representation, köp av inventarier, ägare och närstående, '
        'bokslut, periodiseringar, momsredovisning och skatt, omvänd moms, moms som inte stämmer med 25, 12 eller 6 % av beloppet, '
        'rättelser och kreditnotor, konton som används högst två gånger på året och allt som granskningen ovan har anmärkt på.</p>'
        '<p><b>Gränsen på 25 000 kr gäller inte</b> lön, kundbetalningar som motsvarar en kundfordran i filen och poster som '
        'återkommer med samma text och konton när en människa redan har godkänt dem två gånger (de två första gångerna i filen).</p>'
        '<p>Reglerna är fasta och desamma för alla. Ingen AI har läst din fil.</p></details>'
        '<h3>Uppskattad tidsbesparing</h3>'
        '<div class="kalkyl">'
        f'<label>Minuter per verifikation <input id="konrad-min" type="number" min="0" step="0.5" value="{STANDARD_MINUTER}" inputmode="decimal"></label>'
        '<label>Ditt timpris, kr <input id="konrad-timpris" type="number" min="0" step="50" placeholder="t.ex. 600" inputmode="numeric"></label></div>'
        f'<p class="uttryck" id="konrad-uttryck">{res["auto"]} verifikationer × {STANDARD_MINUTER} minuter ÷ 60 = '
        f'<b id="konrad-timmar">{_dec(t["timmar"])} timmar</b> under perioden i filen.</p>'
        '<p class="uttryck" id="konrad-kronor">Fyll i ditt eget timpris för att se vad tiden är värd.</p>'
        f'<p class="dim">{e(KALLA_MINUTER)} Ändra till det som stämmer för dig. Tiden för de verifikationer som går till en människa räknas inte som sparad, '
        'och du behöver fortfarande lämna kvitton och svara på frågor. Det här är en uppskattning, inget löfte.</p>'
        '<p class="ai-upplysning"><b>Om AI:</b> Konrad är en AI-tjänst. Konrad konterar med hjälp av AI, och nya eller ovanliga poster över 25 000 kr '
        'och poster på ett konto som inte använts förut går till en redovisningskonsult, alltså en människa. Uträkningen här är gjord med fasta regler i din webbläsare, '
        'och din fil har inte lämnat datorn.</p>'
        '<a class="knapp konradknapp" href="/konrad/">Läs om Konrad</a>'
        '<p class="dim" style="margin-top:6px">Konrad drivs av ett annat bolag än AI Auditor, med samma ägare.</p>'
        '</div>')


STIL = """
.konrad{background:#FFFFFF;border:2px solid #1A2A9C;padding:18px 20px;margin:24px 0}
.konrad .etikett{font-family:IBM Plex Mono,monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#1A2A9C;margin:0 0 4px}
.konrad h3{margin:18px 0 6px;font-size:18px}
.konrad ul.skal{margin:6px 0;padding-left:20px}.konrad ul.skal li{margin:4px 0}
.konrad .regler{margin:10px 0;font-size:14px}.konrad .regler summary{cursor:pointer;font-weight:600}
.konrad .kalkyl{display:flex;flex-wrap:wrap;gap:12px;margin:8px 0}
.konrad .kalkyl label{display:flex;flex-direction:column;font-size:14px;font-weight:600;gap:4px}
.konrad .kalkyl input{font:inherit;padding:8px 10px;border:1px solid #C4C9C5;width:150px;max-width:100%}
.konrad .uttryck{font-family:IBM Plex Mono,monospace;font-size:14px;margin:6px 0}
.konrad .ai-upplysning{font-size:13px;border-left:4px solid #1A2A9C;padding:4px 12px;margin:12px 0}
.konrad .konradknapp{background:#1A2A9C}
"""

# Samma formel som tid() – körs i webbläsaren när kunden ändrar minuter eller timpris.
SKRIPT_JS = r"""function konradRakna(rot){var s=rot.getElementById?rot.getElementById('konrad-andel'):null;if(!s)return;
var a=Number(s.getAttribute('data-auto'))||0,mi=rot.getElementById('konrad-min'),tp=rot.getElementById('konrad-timpris');
var m=Number(String(mi.value).replace(',','.'));if(!isFinite(m)||m<0)m=0;var p=Number(String(tp.value).replace(/\s/g,'').replace(',','.'));
var h=a*m/60,f=function(x,d){return x.toLocaleString('sv-SE',{minimumFractionDigits:d,maximumFractionDigits:d});};
rot.getElementById('konrad-uttryck').innerHTML=a+' verifikationer × '+f(m,m%1?1:0)+' minuter ÷ 60 = <b id="konrad-timmar">'+f(h,1)+' timmar</b> under perioden i filen.';
rot.getElementById('konrad-kronor').textContent=(isFinite(p)&&p>0)?(a+' verifikationer × '+f(m,m%1?1:0)+' minuter ÷ 60 × '+f(p,0)+' kr = '+f(Math.round(h*p),0)+' kr (uppskattning)'):'Fyll i ditt eget timpris för att se vad tiden är värd.';}"""
