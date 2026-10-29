#!/usr/bin/env python3
"""Bygger Konrad-sidorna under konrad/ ur konrad-kalla/ (fragment + data). Körs av bygg_sidor.py.

Konrad har EN sajt: aiauditor.se/konrad/ (Olles beslut 29 okt 2026). ~/verket/konrad-sajt är bara källa.
Alla Konrad-sidor är noindex och ligger utanför sajtkarta, llms.txt och flöden tills Olle släpper Konrad.
Priserna kommer ur konrad-kalla/data/konrad-priser.json, funktionerna ur funktioner.json (alla 'vid lansering').
"""
import html, json, re
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
KALLA = ROT / "konrad-kalla"
UT = ROT / "konrad"
UPPDATERAD = "2026-10-29"
GRANSKNING_URL = "/"          # den gratis SIE-granskningen på aiauditor.se
FLYTTADE = {"villkor", "logga-in", "trygghet", "312-kalkylator-2026", "vad-kostar-din-bokforing"}
MENY = [("Kvitton", "/konrad/#kvitton"), ("Priser", "/konrad/#pris"), ("Det här ingår", "/konrad/#ingar"),
        ("3:12-kalkylator", "/konrad/312-kalkylator-2026/"), ("Trygghet", "/konrad/trygghet/"), ("Villkor", "/konrad/villkor/"),
        ("Logga in", "/konrad/logga-in/")]


def e(s):
    return html.escape(str(s), quote=True)


def kr(n):
    return f"{n:,}".replace(",", " ") + " kr"


def las_json(namn):
    return json.loads((KALLA / "data" / f"{namn}.json").read_text(encoding="utf-8"))


def pristrappa(P):
    kort = []
    for n in P["nivaer"]:
        tagg = '<span class="tagg">Med en människa</span>' if n.get("manniska") else ""
        ul = "".join(f"<li>{e(x)}</li>" for x in n["ingar"])
        not_ = f'<p class="liten">{e(n["not"])}</p>' if n.get("not") else ""
        kort.append(f'<div class="niva{" manniska" if n.get("manniska") else ""}">{tagg}<h3>{e(n["namn"])}</h3>'
                    f'<div class="pris">{kr(n["pris"])}<small> /mån exkl. moms</small></div>'
                    f'<p class="vem">{e(n["vem"])}</p><ul>{ul}</ul>{not_}</div>')
    return '<div class="trappa">' + "".join(kort) + "</div>"


def jamforelse(P):
    niv = P["nivaer"]
    hu = "".join(f'<th scope="col">{e(n["namn"])}</th>' for n in niv)
    rader = []
    for i, n in enumerate(niv):
        for x in n["ingar"]:
            celler = "".join(f'<td>{"Ingår" if j >= i else "–"}</td>' for j in range(len(niv)))
            rader.append(f'<tr><th scope="row">{e(x)}</th>{celler}</tr>')
    pris = "".join(f"<td>{kr(n['pris'])}/mån</td>" for n in niv)
    b = "".join(f"<td>{kr(P['bokslut']['pris_ar'])}/år</td>" for n in niv)
    return (f'<div style="overflow-x:auto"><table class="jamfor"><thead><tr><th scope="col">Exkl. moms</th>{hu}</tr></thead><tbody>'
            f'<tr><th scope="row">Pris</th>{pris}</tr>{"".join(rader)}'
            f'<tr><th scope="row">Bokslut och årsredovisning (valfritt hos oss, obligatoriskt för AB)</th>{b}</tr></tbody></table></div>')


def tillval(P):
    def cell(t):
        if t.get("lank"):
            return f'{e(t["text"])}. <a href="{e(t["lank"])}">{e(t.get("lanktext", "Läs mer"))}</a>'
        return e(t["text"])
    return "<table>" + "".join(f"<tr><td>{cell(t)}</td><td>{e(t['pris'])}</td></tr>" for t in P["tillval"]) + "</table>"


def funktioner():
    F = las_json("funktioner")["funktioner"]
    kort = "".join(f'<div data-funktion="{e(f["id"])}"><h3>{e(f["namn"])} <span class="snart">{e(f["status"])}</span></h3>'
                   f'<p class="liten">{e(f["text"])}</p></div>' for f in F)
    return ('<section class="band" id="ingar"><div class="ram">\n  <h2>Det här ingår</h2>\n'
            '  <p class="ingress">Det här är byggt i Konrads motor men används inte av någon kund än. Vilken nivå varje funktion hör till är inte bestämt.</p>\n'
            f'  <div class="funk">{kort}</div>\n</div></section>')


def citera(body, kallor):
    anvanda = []

    def ers(m):
        k = m.group(1)
        if k not in kallor:
            raise SystemExit(f"Okänd källa {{{{k:{k}}}}}")
        if k not in anvanda:
            anvanda.append(k)
        c = kallor[k]
        return (f'<span class="kalla">[<a href="{e(c["url"])}" rel="noopener">{e(c["kort"])}</a>, '
                f'kontrollerad {e(c["datum"])}]</span>')

    body = re.sub(r"\{\{k:([a-z0-9-]+)\}\}", ers, body)
    if anvanda:
        lista = "".join(f'<li><a href="{e(kallor[k]["url"])}" rel="noopener">{e(kallor[k]["namn"])}</a>. '
                        f'Kontrollerad {e(kallor[k]["datum"])}.</li>' for k in anvanda)
        sek = f'<section class="kallor" aria-labelledby="kallor-rub"><h2 id="kallor-rub">Källor</h2><ol>{lista}</ol></section>'
        if '<div class="nasta">' in body:
            body = body.replace('<div class="nasta">', sek + '<div class="nasta">', 1)
        else:
            slut = "</article>" if "</article>" in body else "</div>"
            i = body.rfind(slut)
            body = body[:i] + sek + body[i:]
    return body


def lankar(body, fil):
    """Alla interna länkar ska peka på /konrad/... (eller /, granskningen). Okända länkar är ett fel."""
    def ers(m):
        h = m.group(2)
        if h.startswith(("#", "https://", "http://")):
            if "konradredovisning" in h:
                raise SystemExit(f"{fil}: länk till konradredovisning: {h}")
            return m.group(0)
        if h == "/":
            return m.group(0)
        if h == "/#pris":
            return f'{m.group(1)}/konrad/#pris"'
        if h.startswith("/js/"):
            return f'{m.group(1)}/konrad{h}"'
        slug = h.split("#")[0].strip("/")
        if slug in FLYTTADE:
            return f'{m.group(1)}/konrad{h}"'
        raise SystemExit(f"{fil}: länk till sida som inte finns under /konrad/: {h}")
    return re.sub(r'(\b(?:href|src)=")([^"]*)"', ers, body)


def ram(meta, body):
    nav = "".join(f'<a href="{h}">{e(t)}</a>' for t, h in MENY)
    smul = ""
    if meta["sokvag"]:
        smul = (f'<nav class="smulor ram" aria-label="Du är här"><ol><li><a href="/konrad/">Konrad</a></li>'
                f'<li aria-current="page">{e(meta.get("smula", meta["titel"]))}</li></ol></nav>')
    return f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{e(meta['titel'])}</title>
<meta name="description" content="{e(meta['beskrivning'])}">
<meta name="theme-color" content="#1A2A9C">
<link rel="stylesheet" href="/konrad/konrad.css">
</head>
<body>
<a class="skip" href="#innehall">Hoppa till innehållet</a>
<div class="utkast"><div class="ram">Utkast. Konrad är inte lanserat. Det som är märkt <b>vid lansering</b> finns inte än. Bilderna är bildbanksbilder och byts ut mot riktiga foton före lansering.</div></div>
<header><div class="ram">
  <a class="logga" href="/konrad/"><i aria-hidden="true">K</i>Konrad</a>
  <nav aria-label="Huvudmeny">{nav}</nav>
  <a class="knapp" href="{GRANSKNING_URL}">Granska gratis</a>
</div></header>
{smul}
<main id="innehall">
{body}
</main>
<footer><div class="ram">
  <span>Konrad Redovisning AB (arbetsnamn) · org.nr <span class="platshallare">[fylls i]</span> · <span class="platshallare">[adress]</span> · F-skatt. Fylls i före lansering.</span>
  <span><a href="/konrad/312-kalkylator-2026/">3:12-kalkylator</a> · <a href="/konrad/trygghet/">Så kan du lita på Konrad</a> · <a href="/konrad/villkor/">Villkor</a> · <a href="/konrad/logga-in/">Logga in</a> · <a href="/">AI Auditor</a> · Uppdaterad {UPPDATERAD}{" · Foton: Unsplash (platshållare, byts ut). Siffror och namn i rutorna på bilderna och i kvittoexemplet är påhittade exempel" if meta.get("bildbank") else ""}</span>
</div></footer>
</body>
</html>
"""


def bygg():
    P = las_json("konrad-priser")
    kallor = las_json("kallor")
    antal = 0
    for p in sorted((KALLA / "sidor").glob("*.html")):
        t = p.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", t, re.S)
        meta, body = json.loads(m.group(1)), t[m.end():]
        rep = {"{{GRANSKNING_URL}}": GRANSKNING_URL, "{{UPPDATERAD}}": UPPDATERAD, "{{PRISTRAPPA}}": pristrappa(P),
               "{{TILLVAL}}": tillval(P), "{{JAMFORELSE}}": jamforelse(P), "{{FUNKTIONER}}": funktioner(),
               "{{BOKSLUTSPRIS}}": kr(P["bokslut"]["pris_ar"])}
        for k, v in rep.items():
            body = body.replace(k, v)
        body = re.sub(r"\{\{DATA:([a-z0-9-]+)\}\}",
                      lambda mm: f'<script type="application/json" id="data-{mm.group(1)}">'
                                 f'{json.dumps(las_json(mm.group(1)), ensure_ascii=False).replace("</", "<\\/")}</script>', body)
        body = citera(body, kallor)
        if "{{" in body:
            raise SystemExit(f"{p.name}: okänt makro {re.search(r'{{[^}]*}}', body).group(0)}")
        body = lankar(body, p.name)
        dest = UT / meta["sokvag"] / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(ram(meta, body), encoding="utf-8")
        antal += 1
    print(f"Konrad: {antal} sidor under konrad/")


bygg()
