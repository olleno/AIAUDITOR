"""Bygger branschsidor (SCB) och programguider för aiauditor.se, plus sajtkarta.
Kör från repots rot:  python3 verktyg/bygg_sidor.py
Siffrorna från SCB visas obearbetade ("Källa: SCB"). Branscher med färre än 30 företag, eller med exakt samma
siffror som sin huvudbransch, får ingen egen sida.
"""
import html, json, os, re, shutil, unicodedata
from datetime import date

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCB = json.load(open(os.path.join(ROT, "verktyg", "branschnyckeltal.json"), encoding="utf-8"))
SAJT = "https://aiauditor.se"
AR = SCB["ar"]
e = html.escape
NARINGSLIV = "01-99 exkl 68"
MINST = 30

VISA = [  # scb-kod, kort namn, förklaring
    ("00000340", "Soliditet", "Hur stor del av tillgångarna som är eget kapital. En hög soliditet gör företaget tåligare mot förluster."),
    ("00000343", "Kassalikviditet", "Likvida tillgångar i förhållande till kortfristiga skulder. Under 100 % kan betyda att det blir trångt att betala räkningarna."),
    ("0000032G", "Rörelsemarginal", "Rörelseresultatet i procent av omsättningen: hur mycket som blir kvar av varje intjänad krona efter rörelsens kostnader."),
    ("0000032H", "Nettomarginal", "Resultatet efter finansiella poster i procent av omsättningen."),
    ("0000034A", "Bruttovinstmarginal", "Omsättning minus kostnad för sålda varor, i procent av omsättningen."),
    ("0000033Z", "Personalkostnader / omsättning", "Hur stor del av omsättningen som går till löner och sociala avgifter."),
    ("0000035D", "Kundfordringar / omsättning", "Obetalda kundfakturor i förhållande till årsomsättningen. Ett högt värde betyder att kunderna betalar långsamt."),
    ("0000035F", "Kassa och bank / omsättning", "Likvida medel i förhållande till årsomsättningen."),
    ("0000035G", "Kortfristiga skulder / omsättning", "Skulder som ska betalas inom ett år, i förhållande till årsomsättningen."),
    ("0000035C", "Lager / omsättning", "Lager och pågående arbeten i förhållande till omsättningen."),
    ("0000031V", "Avkastning på eget kapital", "Resultatet i förhållande till det egna kapitalet."),
    ("0000031X", "Avkastning på totalt kapital", "Rörelsens resultat i förhållande till allt kapital i företaget."),
    ("0000039C", "Skuldsättningsgrad", "Skulder delat med eget kapital. Ett högt värde betyder mycket lånade pengar."),
    ("00000345", "Förändring av omsättningen", "Hur mycket omsättningen ökade eller minskade jämfört med året före."),
]
ENHET = {"0000039C": " ggr"}
STORLEKAR = ["001", "1-4", "5-9", "10-19", "20-49", "50-99", "100-199", "200-499", "+500"]

def slug(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:70]

def tal(v, kod):
    if v is None: return "–"
    s = f"{v:,.1f}".replace(",", " ").replace(".", ",")
    if s.endswith(",0"): s = s[:-2]
    return s + ENHET.get(kod, " %")

def antal(kod, st="TOT"):
    t = SCB["data"].get(kod, {}).get(st, {}).get("0000028K")
    return int(t[1]) if t and t[1] is not None else 0

def foralder(k):
    if "." not in k: return None
    a, b = k.split(".")
    p = a if len(b) == 1 else a + "." + b[:-1]
    while p not in SCB["data"] and "." in p:
        p = foralder(p)
    return p if p in SCB["data"] else None

koder = [k for k in SCB["data"] if re.fullmatch(r"\d\d(\.\d+)?", k)]
sidor = {}
for k in sorted(koder, key=lambda x: (x.split(".")[0], x)):
    if antal(k) < MINST: continue
    f = foralder(k)
    if f and SCB["data"][k] == SCB["data"][f]: continue
    sidor[k] = f"{k.replace('.', '-')}-{slug(SCB['sni'][k])}"
def sida_for(k):
    """Närmaste kod uppåt som har en egen sida."""
    while k and k not in sidor: k = foralder(k)
    return k

# ---------- gemensam layout ----------
LOGGA = ('<a href="/" class="logolank" aria-label="AI Auditor, startsidan"><svg class="logo" viewBox="0 0 280 56" role="img" aria-label="AI Auditor">'
 '<path class="m" fill="none" stroke-width="3" stroke-linecap="square" d="M6 17V7h10M40 7h10v10M50 39v10H40M16 49H6V39"/>'
 '<line class="l" x1="15" y1="19" x2="41" y2="19" stroke-width="3" stroke-linecap="round"/><line class="g" x1="15" y1="28" x2="35" y2="28" stroke-width="4" stroke-linecap="round"/>'
 '<line class="l" x1="15" y1="37" x2="41" y2="37" stroke-width="3" stroke-linecap="round"/><circle class="gf" cx="41" cy="28" r="3.5"/>'
 '<text class="gf" x="64" y="32" textLength="27.5" lengthAdjust="spacingAndGlyphs" font-family="Inter, system-ui, sans-serif" font-size="27" font-weight="800">AI</text>'
 '<text class="t" x="98" y="32" textLength="120" lengthAdjust="spacingAndGlyphs" font-family="Inter, system-ui, sans-serif" font-size="27" font-weight="800">AUDITOR</text>'
 '<text class="s" x="65" y="48" textLength="152" lengthAdjust="spacing" font-family="IBM Plex Mono, monospace" font-size="9" font-weight="500">GRANSKNING AV BOKFÖRING</text></svg></a>')

def sida(titel, beskr, kanon, kropp, ld=None):
    ldtxt = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in (ld or []))
    return f'''<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(titel)}</title>
<meta name="description" content="{e(beskr)}">
<link rel="canonical" href="{SAJT}{kanon}">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="article"><meta property="og:locale" content="sv_SE"><meta property="og:site_name" content="AI Auditor">
<meta property="og:url" content="{SAJT}{kanon}"><meta property="og:title" content="{e(titel)}"><meta property="og:description" content="{e(beskr)}">
<meta property="og:image" content="{SAJT}/bilder/delning.jpg"><meta name="twitter:card" content="summary_large_image">
{ldtxt}<script data-goatcounter="https://aiauditor.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Public+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@500&family=Caveat:wght@600&family=Inter:wght@800&display=swap">
<link rel="stylesheet" href="/stil.css">
</head>
<body>
<div class="sida">
<header class="topp">{LOGGA}<nav aria-label="Huvudmeny"><a href="/#granska">Granska</a><a href="/bransch/">Branscher</a><a href="/guider/">Guider</a><a href="/byra/">För byråer</a></nav></header>
<main>
{kropp}
</main>
<footer class="fot"><span>Kansliet at Nordwik Partners · kansliet@nordwikpartners.se</span><span><a href="/bransch/">Nyckeltal per bransch</a> · <a href="/guider/">Ta ut en SIE-fil</a> · <a href="/byra/">För byråer</a></span></footer>
</div>
</body>
</html>
'''

CTA = ('<aside class="cta"><p class="hand">Hur står sig ditt bolag?</p><h2>Jämför din bokföring med {namn}</h2>'
       '<p>Välj SIE-filen från ditt bokföringsprogram. AI Auditor räknar fram samma nyckeltal för ditt bolag, jämför med branschen och går igenom bokföringen med 31 kontroller. Gratis, och filen lämnar aldrig din dator.</p>'
       '<a class="knapp prim" href="/?sni={kod}#granska">Granska och jämför</a></aside>')

def brodsmulor(led):
    li = " › ".join(f'<a href="{u}">{e(n)}</a>' if u else f'<span aria-current="page">{e(n)}</span>' for n, u in led)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, **({"item": SAJT + u} if u else {})} for i, (n, u) in enumerate(led)]}
    return f'<nav class="smulor" aria-label="Du är här">{li}</nav>', ld

# ---------- branschsidor ----------
UT_B = os.path.join(ROT, "bransch")
if os.path.isdir(UT_B): shutil.rmtree(UT_B)
nl = SCB["data"][NARINGSLIV]["TOT"]
barn = {}
for k in sidor:
    f = sida_for(foralder(k)) if foralder(k) else None
    barn.setdefault(f, []).append(k)

for k, s in sidor.items():
    namn = SCB["sni"][k]
    tot = SCB["data"][k]["TOT"]
    n = antal(k)
    def q(kod, i, d=tot):
        v = d.get(kod); return v[i] if v else None
    # sammanfattning i ord, bara SCB:s egna värden
    delar = []
    for kod, kort in (("00000340", "soliditet"), ("0000032G", "rörelsemarginal"), ("00000343", "kassalikviditet")):
        if q(kod, 1) is not None:
            jmf = q(kod, 1, nl)
            delar.append(f"{kort} på {tal(q(kod,1), kod)}" + (f" (näringslivet: {tal(jmf, kod)})" if jmf is not None else ""))
    intro = (f"Medianföretaget inom {namn.lower()} har " + ", ".join(delar[:-1]) + (" och " if len(delar) > 1 else "") + delar[-1] + "." ) if delar else ""
    rader = ""
    for kod, kort, forkl in VISA:
        v = tot.get(kod)
        if not v or all(x is None for x in v): continue
        rader += (f'<tr><th scope="row">{e(kort)}<span class="forkl">{e(forkl)}</span></th><td>{tal(v[0],kod)}</td><td class="med">{tal(v[1],kod)}</td>'
                  f'<td>{tal(v[2],kod)}</td><td class="nl">{tal(q(kod,1,nl),kod)}</td></tr>')
    strad = ""
    for st in STORLEKAR:
        d = SCB["data"][k].get(st)
        if not d: continue
        a = antal(k, st)
        if a < 1: continue
        strad += (f'<tr><th scope="row">{e(SCB["storlek"][st])}</th><td>{a:,}</td>'.replace(",", " ")
                  + "".join(f'<td>{tal((d.get(kod) or [None,None])[1], kod)}</td>' for kod in ("00000340", "0000032G", "00000343", "0000033Z"))
                  + ("<td class='fa'>få företag</td>" if a < MINST else "<td></td>") + "</tr>")
    f = sida_for(foralder(k)) if foralder(k) else None
    led = [("Start", "/"), ("Branscher", "/bransch/")]
    kedja = []
    p = f
    while p: kedja.insert(0, p); p = sida_for(foralder(p)) if foralder(p) else None
    led += [(SCB["sni"][x], f"/bransch/{sidor[x]}/") for x in kedja] + [(namn, None)]
    smul, ldsmul = brodsmulor(led)
    under = "".join(f'<li><a href="/bransch/{sidor[b]}/">{e(SCB["sni"][b])}</a> <span class="kod">{b}</span></li>' for b in barn.get(k, []))
    syskon = [b for b in barn.get(f, []) if b != k][:12]
    syskonhtml = "".join(f'<li><a href="/bransch/{sidor[b]}/">{e(SCB["sni"][b])}</a></li>' for b in syskon)
    kropp = (smul +
        f'<article><p class="etikett">Nyckeltal per bransch · SNI {k}</p><h1>Nyckeltal för {e(namn.lower())}</h1>'
        f'<p class="ingress">{e(intro)} Siffrorna bygger på {n:,} företag och avser år {AR}.</p>'.replace(f"{n:,}", f"{n:,}".replace(",", " ")) +
        f'<h2>Så ser branschen ut</h2><div class="tabell"><table><thead><tr><th>Nyckeltal</th><th>Undre kvartil</th><th>Median</th><th>Övre kvartil</th><th>Näringslivet, median</th></tr></thead><tbody>{rader}</tbody></table></div>'
        '<p class="not">Medianen är värdet för företaget i mitten. Hälften av företagen ligger mellan undre och övre kvartil. Kvartilerna anges som SCB redovisar dem. "Näringslivet" är hela bolagssektorn utom fastighetsförvaltning.</p>'
        + CTA.format(namn=e(namn.lower()), kod=k) +
        (f'<h2>Efter företagets storlek</h2><p>Mediantal per storleksklass, efter antal anställda.</p><div class="tabell"><table><thead><tr><th>Storlek</th><th>Företag</th><th>Soliditet</th><th>Rörelsemarginal</th><th>Kassalikviditet</th><th>Personalkostnader / omsättning</th><th></th></tr></thead><tbody>{strad}</tbody></table></div>' if strad else '')
        + (f'<h2>Underbranscher</h2><ul class="lankar">{under}</ul>' if under else '')
        + (f'<h2>Närliggande branscher</h2><ul class="lankar">{syskonhtml}</ul>' if syskonhtml else '')
        + f'<p class="kalla">Källa: SCB, Företagens ekonomi (tabell BNTT01), år {AR}. Branschindelning enligt SNI 2007.</p></article>')
    ld = [ldsmul, {"@context": "https://schema.org", "@type": "Dataset", "name": f"Nyckeltal för {namn.lower()} {AR}",
           "description": f"Branschnyckeltal (kvartiler) för SNI {k} {namn}, {AR}, från SCB:s Företagens ekonomi.",
           "creator": {"@type": "Organization", "name": "Statistiska centralbyrån (SCB)", "url": "https://www.scb.se"},
           "license": "https://creativecommons.org/publicdomain/zero/1.0/", "temporalCoverage": str(AR), "inLanguage": "sv",
           "url": f"{SAJT}/bransch/{s}/"}]
    titel = f"Nyckeltal för {namn.lower()} {AR} – soliditet, marginaler, likviditet"
    beskr = (f"{namn}: {intro} Jämför ditt bolag gratis med branschen.")[:300]
    os.makedirs(os.path.join(UT_B, s), exist_ok=True)
    open(os.path.join(UT_B, s, "index.html"), "w", encoding="utf-8").write(sida(titel, beskr, f"/bransch/{s}/", kropp, ld))

# översikt
grupper = ""
for k in [x for x in sidor if "." not in x] + sorted({x.split(".")[0] for x in sidor if "." in x and x.split(".")[0] not in sidor}):
    rubrik = SCB["sni"].get(k, k)
    lista = [x for x in sidor if x.split(".")[0] == k.split(".")[0] and x != k]
    huvud = f'<a href="/bransch/{sidor[k]}/">{e(rubrik)}</a>' if k in sidor else e(rubrik)
    grupper += (f'<section class="grupp"><h2><span class="kod">{k}</span> {huvud}</h2>'
                + (f'<ul class="lankar">' + "".join(f'<li><a href="/bransch/{sidor[x]}/">{e(SCB["sni"][x])}</a> <span class="kod">{x}</span></li>' for x in lista) + '</ul>' if lista else '') + '</section>')
smul, ldsmul = brodsmulor([("Start", "/"), ("Branscher", None)])
kropp = (smul + f'<article><p class="etikett">Nyckeltal per bransch</p><h1>Hur går det för branschen?</h1>'
         f'<p class="ingress">Soliditet, marginaler, likviditet och betalningstider för {len(sidor)} branscher, från SCB:s statistik över företagens ekonomi år {AR}. Välj en bransch, eller <a href="/#granska">jämför ditt eget bolag direkt</a>.</p>'
         + grupper + f'<p class="kalla">Källa: SCB, Företagens ekonomi (tabell BNTT01), år {AR}.</p></article>')
os.makedirs(UT_B, exist_ok=True)
open(os.path.join(UT_B, "index.html"), "w", encoding="utf-8").write(
    sida(f"Nyckeltal per bransch {AR} – soliditet och marginaler för {len(sidor)} branscher", f"Branschnyckeltal från SCB för {len(sidor)} branscher: soliditet, rörelsemarginal, kassalikviditet med mera. Jämför ditt bolag gratis.", "/bransch/", kropp, [ldsmul]))

# ---------- programguider ----------
from guider_data import GUIDER
UT_G = os.path.join(ROT, "guider")
if os.path.isdir(UT_G): shutil.rmtree(UT_G)
for g in GUIDER:
    smul, ldsmul = brodsmulor([("Start", "/"), ("Guider", "/guider/"), (g["namn"], None)])
    steg = "".join(f"<li><span>{x}</span></li>" for x in g["steg"])
    extra = "".join(f"<li>{x}</li>" for x in g.get("tips", []))
    kallor = "".join(f'<li><a href="{u}" rel="nofollow noopener">{e(t)}</a></li>' for t, u in g["kallor"])
    howto = {"@context": "https://schema.org", "@type": "HowTo", "name": f"Exportera SIE-fil från {g['namn']}", "inLanguage": "sv",
             "step": [{"@type": "HowToStep", "position": i + 1, "text": re.sub("<[^>]+>", "", x)} for i, x in enumerate(g["steg"])]}
    kropp = (smul + f'<article class="guide"><p class="etikett">Guide · {e(g["namn"])}</p><h1>Så tar du ut en SIE-fil från {e(g["namn"])}</h1>'
             f'<p class="ingress">{g["ingress"]}</p><h2>Steg för steg</h2><ol class="steg">{steg}</ol>'
             + (f'<h2>Bra att veta</h2><ul>{extra}</ul>' if extra else '')
             + CTA.format(namn="branschen", kod="").replace("?sni=#granska", "#granska").replace("Jämför din bokföring med branschen", "Granska filen du just tog ut").replace("Hur står sig ditt bolag?", "Nästa steg").replace("Granska och jämför", "Granska bokföringen")
             + f'<h2>Källor</h2><p>Menyvägen kommer från leverantörens egen hjälp. Program uppdateras ibland, så namnen kan skilja sig något.</p><ul>{kallor}</ul>'
             f'<p class="not">Senast kontrollerad {date.today().isoformat()}.</p></article>')
    os.makedirs(os.path.join(UT_G, g["slug"]), exist_ok=True)
    open(os.path.join(UT_G, g["slug"], "index.html"), "w", encoding="utf-8").write(
        sida(f"Exportera SIE-fil från {g['namn']} – steg för steg", f"Så exporterar du en SIE-fil (typ 4) från {g['namn']}: menyvägen steg för steg, och hur du sedan granskar bokföringen gratis.", f"/guider/{g['slug']}/", kropp, [ldsmul, howto]))
smul, ldsmul = brodsmulor([("Start", "/"), ("Guider", None)])
lista = "".join(f'<li><a href="/guider/{g["slug"]}/">Exportera SIE-fil från {e(g["namn"])}</a></li>' for g in GUIDER)
kropp = (smul + '<article><p class="etikett">Guider</p><h1>Så tar du ut en SIE-fil</h1>'
         '<p class="ingress">SIE är det svenska standardformatet för bokföring. Alla svenska bokföringsprogram kan spara bokföringen som en SIE-fil, och det är den filen du behöver för att granska bokföringen i AI Auditor. Välj typ 4, som innehåller alla verifikationer, och ett räkenskapsår i taget.</p>'
         f'<h2>Välj ditt program</h2><ul class="lankar stora">{lista}</ul>'
         '<h2>Står inte ditt program med?</h2><p>Leta efter <strong>Export</strong>, <strong>Import och export</strong> eller <strong>SIE</strong> i menyerna, ofta under Arkiv, Inställningar eller Bokföring. Välj SIE typ 4 och hela räkenskapsåret. Filen slutar oftast på <code>.se</code>.</p></article>')
os.makedirs(UT_G, exist_ok=True)
open(os.path.join(UT_G, "index.html"), "w", encoding="utf-8").write(
    sida("Så tar du ut en SIE-fil – guider för Fortnox, Bokio, Spiris med flera", "Steg-för-steg-guider för att exportera en SIE-fil (typ 4) från Fortnox, Spiris, Visma Administration, Bokio, Björn Lundén, Accounted och Briox.", "/guider/", kropp, [ldsmul]))

# ---------- byråsidan ----------
import byra_sida
byra_sida.bygg(sida, brodsmulor, ROT)

# ---------- sajtkarta ----------
idag = date.today().isoformat()
urls = ["/", "/byra/", "/bransch/", "/guider/"] + [f"/guider/{g['slug']}/" for g in GUIDER] + [f"/bransch/{s}/" for s in sidor.values()]
open(os.path.join(ROT, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"<url><loc>{SAJT}{u}</loc><lastmod>{idag}</lastmod></url>\n" for u in urls) + "</urlset>\n")
print(f"{len(sidor)} branschsidor, {len(GUIDER)} guider, {len(urls)} adresser i sajtkartan")
