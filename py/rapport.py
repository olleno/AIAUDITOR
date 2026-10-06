"""AI Auditor – rapport med trafikljus, tre vyer (själv / byrå / revisor), nyckeltal mot SCB och råd.

Kör:  python3 -I rapport.py bokforing.se rapport.html [--sni 58110] [--idag ÅÅÅÅ-MM-DD]
"""
import html, os, re, sys
from datetime import date as _d
from datetime import date
HÄR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HÄR)
import granskaren as g
import nyckeltal as n

e = html.escape
kr0 = lambda x: f"{x:,.0f}".replace(",", " ")

VARFOR = {
    "Grundbokföring": "Bokföringen ska vara fullständig och gå att följa från verifikation till rapport. Brister här gör att siffrorna inte går att lita på.",
    "Moms": "Fel i momsen ger fel momsdeklaration. Skatteverket kan ta ut skattetillägg och ränta på det som redovisats för lite.",
    "Skatt": "Fel här påverkar bolagets eller ägarens skatt och kan ge skattetillägg.",
    "Lön": "Löner, skatteavdrag och arbetsgivaravgifter redovisas varje månad till Skatteverket. Fel ger fel arbetsgivardeklaration.",
    "Avskrivningar": "Felaktiga avskrivningar ger fel resultat och därmed fel skatt.",
    "Bank och kassa": "Bank och kassa är det lättaste att stämma av – avvikelser här tyder ofta på fel någon annanstans.",
    "Aktiebolag": "Aktiebolagslagen ställer krav som styrelsen personligen kan bli ansvarig för.",
    "Bokslut": "Bokslutet ska stämma med bokföringen och lämnas in i tid.",
}
STATUS = {
    "rod": ("#9B2C1F", "Rött", "Det finns fel som bör rättas", "Felen kan påverka skatt, moms eller styrelsens ansvar. Gå igenom dem innan nästa deklaration eller bokslut."),
    "gul": ("#9A6A12", "Gult", "Några saker bör kontrolleras", "Inget tyder på allvarliga fel, men några poster bör kontrolleras och vid behov rättas före bokslutet."),
    "gron": ("#4E7A45", "Grönt", "Inga anmärkningar i de kontroller vi gjort", "Det betyder inte att allt är rätt – se vad som inte har kontrollerats längre ner. Kör granskningen igen nästa kvartal."),
}
TAG = {1: ("Fel", "#9B2C1F"), 2: ("Kontrollera", "#9A6A12"), 3: ("Notering", "#6B726E")}
BED = {"bra": ("Bättre än de flesta", "#4E7A45"), "svag": ("Sämre än de flesta", "#9B2C1F"),
       "normal": ("Som branschen", "#4A524D"), "neutral": ("", "#4A524D")}
LAGE = ["under de flesta", "under mitten", "över mitten", "över de flesta"]

LOGGA = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 56" width="220" role="img" aria-label="AI Auditor">'
  '<g fill="none" stroke="#1E3A31" stroke-width="3" stroke-linecap="square"><path d="M6 17V7h10M40 7h10v10M50 39v10H40M16 49H6V39"/></g>'
  '<g stroke-linecap="round"><line x1="15" y1="19" x2="41" y2="19" stroke="#A9B0AB" stroke-width="3"/>'
  '<line x1="15" y1="28" x2="35" y2="28" stroke="#4E7A45" stroke-width="4"/><line x1="15" y1="37" x2="41" y2="37" stroke="#A9B0AB" stroke-width="3"/></g>'
  '<circle cx="41" cy="28" r="3.5" fill="#4E7A45"/>'
  '<text x="64" y="32" textLength="27.5" lengthAdjust="spacingAndGlyphs" font-family="Inter, system-ui, sans-serif" font-size="27" font-weight="800" letter-spacing="-0.5" fill="#4E7A45">AI</text>'
  '<text x="98" y="32" textLength="120" lengthAdjust="spacingAndGlyphs" font-family="Inter, system-ui, sans-serif" font-size="27" font-weight="800" letter-spacing="-0.5" fill="#1E3A31">AUDITOR</text>'
  '<text x="65" y="48" textLength="152" lengthAdjust="spacing" font-family="IBM Plex Mono, monospace" font-size="9" font-weight="500" fill="#4A524D">GRANSKNING AV BOKFÖRING</text></svg>')
FOTTEXT = '<div class="fot">Kansliet at Nordwik Partners</div>'

EXTRA_STIL = """
.status{color:#fff;padding:20px 22px;margin:20px 0}.status b{font-size:22px;display:block;font-weight:800}
.vyer{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.vyer button{font:inherit;font-weight:600;padding:10px 16px;border:1px solid var(--mork);background:var(--vit);color:var(--mork);cursor:pointer}
.vyer button.aktiv{background:var(--mork);color:#fff}
.vy{display:none}.vy.aktiv{display:block}
.fynd{background:var(--vit);border:1px solid var(--linje);padding:16px 18px;margin:10px 0}
.fynd h3{margin:4px 0 6px;font-size:17px}.fynd dl{display:grid;grid-template-columns:130px 1fr;gap:4px 12px;margin:8px 0 0}
.fynd dt{color:var(--dim);font-size:13px}.fynd dd{margin:0}
.bock{display:flex;gap:8px;align-items:center;margin-top:10px;font-weight:600}
.stapel{position:relative;height:10px;background:linear-gradient(90deg,#E9E6DF 0 25%,#DAD6CC 25% 75%,#E9E6DF 75%);min-width:140px}
.stapel i{position:absolute;top:-4px;width:4px;height:18px;background:var(--mork);margin-left:-2px}
.stapel s{position:absolute;top:0;width:1px;height:10px;background:#8a8f8b;left:50%}
.brev{background:var(--vit);border:1px solid var(--linje);padding:22px 24px}.brev li{margin:10px 0}
.cta{background:var(--mork);color:#fff;padding:20px 22px;margin:24px 0}.cta a{color:#fff;font-weight:700}
.knapp{display:inline-block;background:var(--gron);color:#fff;padding:10px 16px;font-weight:700;text-decoration:none;margin:6px 8px 0 0}
.meta{color:var(--dim);font-size:13px;margin-top:2px}
.ansvar{font-size:13px;color:var(--sek);border-left:4px solid var(--linje);padding:4px 12px;margin:12px 0}
@media print{.vyer,.knapp,.cta .knapp{display:none}.vy{display:none}.vy.aktiv{display:block}body{background:#fff}}
@media(max-width:700px){.fynd dl{grid-template-columns:1fr}}
"""
SKRIPT = """<script>
function vy(id){document.querySelectorAll('.vy').forEach(function(x){x.classList.toggle('aktiv',x.id===id)});
document.querySelectorAll('.vyer button[data-vy]').forEach(function(b){b.classList.toggle('aktiv',b.dataset.vy===id)});}
document.addEventListener('click',function(ev){if(ev.target.id!=='kopiera-ai')return;var t=document.getElementById('ai-underlag'),i=document.getElementById('kopierat-ai');
try{navigator.clipboard.writeText(t.value).then(function(){i.textContent='Kopierat. Klistra in i din AI-tjänst.';},function(){t.select();i.textContent='Markerat. Kopiera med Cmd+C eller Ctrl+C.';});}catch(e){t.select();i.textContent='Markerat. Kopiera med Cmd+C eller Ctrl+C.';}});
</script>"""

AI_INSTRUKTION = """Du är en noggrann granskare av svensk bokföring. Nedan finns bokföringen för ett företag, uttagen ur en SIE-fil, samt det en automatisk regelgranskning redan har hittat.

Uppgift: Leta efter sådant som fasta regler lätt missar. Till exempel:
- verifikationer där kontot inte passar texten (t.ex. en privat vara på ett kostnadskonto, en investering som kostnadsförts)
- momssats som inte passar varan eller tjänsten enligt texten (t.ex. livsmedel, böcker, persontransporter, hotell)
- kostnader som kan vara privata eller inte avdragsgilla
- kostnader eller intäkter som borde periodiseras till ett annat år
- återkommande kostnader som saknas en eller flera månader, eller dyker upp dubbelt
- ovanliga belopp, mottagare eller mönster jämfört med resten av bokföringen

Regler för svaret:
- Svara på svenska, högst 15 punkter, viktigast först.
- Varje punkt: verifikationsnummer, vad du ser, varför det kan vara fel, och vad som bör kontrolleras.
- Upprepa inte det regelgranskningen redan har hittat.
- Hänvisa bara till lagrum du är säker på. Skriv hellre "bör kontrolleras" än att gissa.
- Räkna inte om summor eller saldon. Utgå från beloppen som de står.
- Om underlaget inte räcker för en bedömning, säg det.
- Det här är en granskning, inte en revision. Ansvaret för bokföringen ligger hos företaget."""

def ai_underlag(bok, fynd, max_tecken=60000):
    """Färdig text att klistra in i en egen AI-tjänst: instruktion, redan funna fel och verifikationerna."""
    kr2 = lambda x: f"{x:,.2f}".replace(",", " ").replace(".", ",")
    knamn = bok["konton"]
    rar = f"{bok['rar'][0]} – {bok['rar'][1]}" if bok["rar"] else "okänt"
    redan = "\n".join(f"- {f['ver'] if f['ver'] != '–' else 'Allmänt'}: {f['rubrik']} – {f['beskr']}" for f in fynd) or "- Inga"
    def rad(v):
        delar = "; ".join(f"{k} {knamn.get(k, '')} {kr2(b)}".replace("  ", " ") for k, b in v["rader"])
        return f"{v['serie']}{v['nr']} | {v['datum']} | {v['text']} | {delar}"
    rader = [rad(v) for v in bok["ver"]]
    urval = ""
    if sum(len(r) for r in rader) > max_tecken:
        flaggade = {f["ver"] for f in fynd}
        storlek = lambda v: max((abs(b) for _, b in v["rader"]), default=0)
        valda = [v for v in bok["ver"] if f"{v['serie']}{v['nr']}" in flaggade]
        for v in sorted(bok["ver"], key=storlek, reverse=True):
            if sum(len(rad(x)) for x in valda) > max_tecken: break
            if v not in valda: valda.append(v)
        valda.sort(key=lambda v: (v["datum"] or _d.min, str(v["nr"])))
        rader = [rad(v) for v in valda]
        urval = f" (urval: {len(valda)} av {len(bok['ver'])} verifikationer – de som regelgranskningen flaggat och de med störst belopp)"
    return (AI_INSTRUKTION + f"\n\nFÖRETAG: {bok['namn']} ({bok['orgnr']}), räkenskapsår {rar}\n\n"
            f"REDAN FUNNET AV REGELGRANSKNINGEN:\n{redan}\n\n"
            f"VERIFIKATIONER{urval}\nFormat: nummer | datum | text | konto kontonamn belopp (debet positivt, kredit negativt)\n" + "\n".join(rader))

def _pos(r):
    uk, med, ok = r["uk"], r["med"], r["ok"]
    v = r["varde"]
    spann = max(ok - uk, 1e-9)
    if v < uk: p = max(0, 25 - (uk - v) / spann * 50)
    elif v < med: p = 25 + (v - uk) / max(med - uk, 1e-9) * 25
    elif v <= ok: p = 50 + (v - med) / max(ok - med, 1e-9) * 25
    else: p = min(100, 75 + (v - ok) / spann * 50)
    return p

def _tal(v, enhet):
    return (f"{v:,.1f}".replace(",", " ").replace(".", ",") + (" %" if enhet == "%" else " ggr"))

def bygg(bok, fynd, idag, sni=None, webb=False):
    berak = n.berakna(bok, idag)
    jmf = n.jamfor(berak, sni) if sni else None
    rad = n.rad(berak, jmf)
    status = "rod" if any(f["allvar"] == 1 for f in fynd) else "gul" if any(f["allvar"] == 2 for f in fynd) else "gron"
    farg, ord_, rub, txt = STATUS[status]
    rar = f"{bok['rar'][0]} – {bok['rar'][1]}" if bok["rar"] else "okänt"
    avst = bok.get("_avstamning") or []
    gjorda = {r[0] for r in avst}
    aktiva = [r for r in g.KATALOG.values() if r["status"] == "aktiv" and (r["lager"] == "1" or r["id"] in gjorda)]
    antal = {k: sum(1 for f in fynd if f["allvar"] == k) for k in (1, 2, 3)}

    # --- fyndkort ---
    def kort(f, bock):
        t, c = TAG[f["allvar"]]
        var = f'Verifikation {e(f["ver"])}, {e(f["datum"])}' if f["ver"] != "–" else "Hela bokföringen"
        if f["text"]: var += f' – ”{e(f["text"])}”'
        return (f'<div class="fynd"><span class="tag" style="background:{c}">{t}</span> <span class="dim">{e(f["omrade"])}</span>'
                f'<h3>{e(f["rubrik"])}</h3><dl><dt>Var</dt><dd>{var}</dd><dt>Vad</dt><dd>{e(f["beskr"])}</dd>'
                f'<dt>Varför det spelar roll</dt><dd>{e(VARFOR.get(f["omrade"], ""))} <span class="dim">Regel: {e(f["kalla"])}</span></dd>'
                f'<dt>Förslag</dt><dd>{e(f["forslag"])}</dd></dl>'
                + ('<label class="bock"><input type="checkbox"> Åtgärdat</label>' if bock else '') + '</div>')

    # --- nyckeltal ---
    if jmf and jmf["rader"]:
        nrader = "".join(
            f'<tr><td><strong>{e(r["namn"])}</strong><br><span class="dim">{e(r["forkl"])}</span></td>'
            f'<td class="mono">{_tal(r["varde"], r["enhet"])}</td><td class="mono">{_tal(r["med"], r["enhet"])}</td>'
            f'<td><div class="stapel"><s></s><i style="left:{_pos(r):.0f}%"></i></div><span class="dim">{LAGE[r["lage"]]}</span></td>'
            f'<td style="color:{BED[r["bed"]][1]};font-weight:600">{BED[r["bed"]][0]}</td></tr>' for r in jmf["rader"])
        storl = jmf["storlek_text"] + (" (uppskattat från lönekostnaderna)" if jmf["uppskattad_storlek"] and jmf["storlek"] != "TOT" else "")
        nyck = (f'<h2>Så står ni er mot branschen</h2><p class="sub">Jämfört med {jmf["antal"]} företag inom '
                f'<strong>{e(jmf["sni_text"].lower())}</strong>, {e(storl)}. Källa: {e(jmf["kalla"])}, år {jmf["ar"]}. '
                f'Stapeln visar var ni hamnar: mittstrecket är branschens median, det mörka fältet är mittenhälften av företagen.</p>'
                + (f'<div class="ansvar">Räkenskapsåret pågår – bokföringen omfattar {berak["manader"]} månader. Belopp som jämförs med omsättningen är omräknade till helår och därför osäkrare.</div>' if berak["delar"] else '')
                + f'<table><tr><th>Nyckeltal</th><th>Ni</th><th>Branschens median</th><th>Läge</th><th>Bedömning</th></tr>{nrader}</table>'
                f'<p class="dim">Nyckeltalen räknas ur bokföringsfilen med vanliga definitioner. SCB:s definitioner kan skilja något, så se jämförelsen som en fingervisning.</p>')
    else:
        nyck = '<h2>Så står ni er mot branschen</h2><p class="sub">Ange bransch (SNI-kod) för att jämföra med SCB:s statistik.</p>'

    radhtml = ("<h2>Enkla råd</h2>" + "".join(f'<div class="fynd"><h3>{e(a)}</h3>{e(b)}</div>' for a, b in rad)) if rad else ""

    ej = [t for regel, t in (("MO11", "momsdeklarationer"), ("SK05", "skattekontot"), ("BA03", "bankens saldon"), ("BO01", "bokslutet")) if regel not in gjorda]
    jamfort = [t for regel, t in (("MO11", "momsdeklarationer"), ("SK05", "skattekontot"), ("BA03", "bankens saldon"), ("BO01", "bokslutet")) if regel in gjorda]
    lista = lambda xs: (", ".join(xs[:-1]) + " och " + xs[-1]) if len(xs) > 1 else (xs[0] if xs else "")
    ejkoll = ('<div class="ruta"><strong>Det här har vi inte kontrollerat.</strong> Granskningen bygger på bokföringsfilen (SIE)'
              + (f' och de uppgifter du fyllt i om {lista(jamfort)}' if jamfort else '') + '. Kvitton, fakturor och avtal har inte setts. '
              + (f'{lista(ej).capitalize()} har inte jämförts' + (' – <a href="#avstam" data-oppna="avstam">fyll i dem och granska igen</a>. ' if webb else '. ') if ej else '')
              + f'Därför kan fel finnas som inte syns här. {len(aktiva)} kontroller har körts.</div>')
    if avst:
        k2 = lambda x: g.kr(0.0 if abs(x) < 0.005 else x)
        avrader = "".join(f'<tr><td>{e(vad)}</td><td class="mono">{k2(doc)}</td><td class="mono">{k2(bk)}</td><td class="mono">{k2(diff)}</td>'
                          f'<td style="color:{"#4E7A45" if ok else "#9B2C1F"};font-weight:600">{"Stämmer" if ok else "Avviker"}</td></tr>'
                          for regel, vad, doc, bk, diff, ok in avst)
        avsektion = ('<h2>Avstämning mot dina handlingar</h2><table><tr><th>Vad</th><th>Enligt handlingen</th><th>Enligt bokföringen</th><th>Skillnad</th><th>Resultat</th></tr>'
                     + avrader + '</table><p class="dim">Belopp i kronor. Avvikelser finns också som fynd ovan, med förslag på vad du kan göra.</p>')
    else:
        avsektion = ""
    ansvar_kort = '<div class="ansvar">Det här är förslag från en automatisk granskning, inte en revision. Det är du eller styrelsen som ansvarar för bokföringen och bestämmer vad som ska ändras.</div>'
    ansvar_hel = ('<h2>Ansvar</h2><p>Rapporten är framtagen automatiskt utifrån bokföringsfilen och svensk lag och praxis. Den är inte en revision och ersätter inte revisor. '
                  'Ansvaret för bokföringen ligger hos den bokföringsskyldige – i ett aktiebolag styrelsen och vd (aktiebolagslagen 8 kap 4 och 29 §§). '
                  'Kontrollera varje förslag mot underlaget innan du ändrar något. Rätta alltid med en ny rättelseverifikation – ändra eller radera aldrig den ursprungliga '
                  '(bokföringslagen 5 kap 5 §).</p>')

    if status == "gron":
        cta = ('<div class="cta"><b>Vad gör jag nu?</b><br>Spara rapporten och kör granskningen igen nästa kvartal.'
               '<br><a class="knapp" href="#" onclick="window.print();return false">Spara som PDF</a></div>')
    else:
        cta = ('<div class="cta"><b>Vad gör jag nu?</b><br>Rätta själv med förslagen ovan, skicka sammanfattningen till din byrå – '
               'eller låt oss rätta det och sköta bokföringen framåt.<br>'
               '<a class="knapp" href="#" onclick="vy(\'byra\');return false">Visa sammanfattning till byrån</a>'
               '<a class="knapp" href="mailto:kansliet@nordwikpartners.se?subject=Hj%C3%A4lp%20efter%20granskning&amp;body=Hej!%20Jag%20har%20granskat%20bokf%C3%B6ringen%20i%20AI%20Auditor%20och%20vill%20ha%20hj%C3%A4lp%20att%20r%C3%A4tta%20och%20sk%C3%B6ta%20den%20fram%C3%A5t.">Låt Kansliet sköta det</a>'
               '<br><span style="font-size:13px;opacity:.85">Eller mejla kansliet@nordwikpartners.se</span></div>')

    underlag = ai_underlag(bok, fynd)
    aisektion = ('<h2>Fördjupa med din egen AI</h2><div class="fynd">'
                 '<p>Regelgranskningen hittar det som går att kontrollera med fasta regler. En AI kan dessutom läsa verifikationstexterna och se sådant som '
                 'inte passar, till exempel fel konto, fel momssats eller kostnader som kan vara privata.</p>'
                 '<p><strong>Så gör du:</strong> kopiera underlaget nedan och klistra in det i den AI-tjänst du själv använder, till exempel ChatGPT, Claude eller Gemini.</p>'
                 f'<textarea id="ai-underlag" readonly rows="8" style="width:100%;font-family:IBM Plex Mono,monospace;font-size:12px;padding:10px;border:1px solid #C4C9C5;background:#F4F3EF;color:#141A16">{e(underlag)}</textarea>'
                 '<div><button class="knapp" id="kopiera-ai" type="button" style="border:0;cursor:pointer;font:inherit;font-weight:700">Kopiera underlaget</button> <span class="dim" id="kopierat-ai"></span></div>'
                 '<p class="dim" style="margin-top:8px">Underlaget innehåller bolagets verifikationer med texter och belopp. Det skickas bara till den AI-tjänst du själv väljer, '
                 'och hanteras enligt den tjänstens villkor. AI:ns svar är förslag att kontrollera, inte fastställda fel.</p></div>')

    # --- vyer ---
    sjalv = ('<div id="sjalv" class="vy aktiv"><h2>Att åtgärda</h2>' +
             ("".join(kort(f, True) for f in fynd) or '<p>Inga anmärkningar.</p>') + avsektion + nyck + radhtml + aisektion + cta + '</div>')
    fragor = "".join(f'<li><strong>{("Ver " + e(f["ver"]) + " (" + e(f["datum"]) + ")") if f["ver"] != "–" else "Allmänt"}:</strong> '
                     f'{e(f["beskr"])} Kan ni titta på om det stämmer och om något behöver rättas?</li>'
                     for f in fynd if f["allvar"] <= 2)
    noter = [f for f in fynd if f["allvar"] == 3]
    byra = (f'<div id="byra" class="vy"><div class="brev"><p>Hej!</p><p>Vi har kört en automatisk granskning av bokföringen för '
            f'{e(bok["namn"])} ({e(bok["orgnr"])}), räkenskapsår {rar}. Den hittade några saker som vi skulle vilja att ni tittar på:</p>'
            f'<ol>{fragor or "<li>Inga frågor – granskningen hittade inget att anmärka på.</li>"}</ol>'
            + (f'<p>Dessutom {len(noter)} {"mindre notering" if len(noter) == 1 else "mindre noteringar"}, se bifogad rapport.</p>' if noter else '') +
            '<p>Det kan finnas förklaringar som inte syns i bokföringsfilen. Hör gärna av er om något är oklart.</p><p>Med vänlig hälsning</p></div>'
            '<p class="dim">Kopiera texten till ett mejl, eller spara som PDF och bifoga.</p>'
            '<a class="knapp" href="#" onclick="window.print();return false">Spara som PDF</a></div>')
    regelrader = "".join(f'<tr><td class="mono">{r["id"]}</td><td>{e(r["regel"])}</td><td>{e(r["kalla"])}</td>'
                         f'<td>{"<strong>" + str(sum(1 for f in fynd if f["regel"] == r["id"])) + " fynd</strong>" if any(f["regel"] == r["id"] for f in fynd) else "Inga fynd"}</td></tr>'
                         for r in aktiva)
    revisor = ('<div id="revisor" class="vy"><h2>Fynd</h2>' + ("".join(kort(f, False) for f in fynd) or "<p>Inga fynd.</p>") +
               avsektion + f'<h2>Kontroller som har körts</h2><table><tr><th>Id</th><th>Kontroll</th><th>Regel</th><th>Utfall</th></tr>{regelrader}</table>'
               + nyck + '<a class="knapp" href="#" onclick="window.print();return false">Spara som PDF</a></div>')

    kropp = (LOGGA +
            f'<h1>Granskningsrapport</h1><div class="sub">Granskat företag: {e(bok["namn"])}</div>'
            f'<div class="meta">Org.nr {e(bok["orgnr"])} · Räkenskapsår {rar} · Granskad {idag}</div>'
            + ansvar_kort +
            f'<div class="status" style="background:{farg}"><span style="opacity:.85;font-size:13px">Samlad bedömning: {ord_}</span><b>{rub}</b>{txt}</div>'
            f'<div class="kort"><div class="k"><b>{len(bok["ver"])}</b>verifikationer</div><div class="k"><b style="color:#9B2C1F">{antal[1]}</b>fel</div>'
            f'<div class="k"><b style="color:#9A6A12">{antal[2]}</b>att kontrollera</div><div class="k"><b style="color:#6B726E">{antal[3]}</b>noteringar</div></div>'
            '<div class="vyer"><button data-vy="sjalv" class="aktiv" onclick="vy(\'sjalv\')">Jag bokför själv</button>'
            '<button data-vy="byra" onclick="vy(\'byra\')">Sammanfattning till min byrå</button>'
            '<button data-vy="revisor" onclick="vy(\'revisor\')">Underlag till revisor</button></div>'
            + sjalv + byra + revisor + ejkoll + ansvar_hel + FOTTEXT)
    if webb:
        # På sajten: inga utskriftsknappar (fungerar inte där), i stället kopiera-knapp för byråtexten
        kropp = kropp.replace('<a class="knapp" href="#" onclick="window.print();return false">Spara som PDF</a>', '')
        kropp = kropp.replace('<p class="dim">Kopiera texten till ett mejl, eller spara som PDF och bifoga.</p>',
                              '<button class="knapp" id="kopiera-byra" type="button">Kopiera texten</button> <span class="dim" id="kopierat"></span>')
        kropp = re.sub(r'onclick="vy\(\'(\w+)\'\)(;return false)?"', r'data-vy="\1"', kropp)
        kropp = kropp.replace('href="#" data-vy', 'href="#rapport" data-vy')
        return g.STIL + EXTRA_STIL, kropp
    huvud = g.HUVUD.replace("TITEL", "AI Auditor – granskningsrapport").replace("</style>", EXTRA_STIL + "</style>").replace(g.LOGGA, "")
    return huvud + kropp + SKRIPT + "</div></body></html>"

def norm_sni(s):
    s = "".join(c for c in (s or "") if c.isdigit())
    return s[:2] + ("." + s[2:] if len(s) > 2 else "") if s else None

if __name__ == "__main__":
    args = sys.argv[1:]
    sni = norm_sni(args[args.index("--sni") + 1]) if "--sni" in args else None
    idag = date.fromisoformat(args[args.index("--idag") + 1]) if "--idag" in args else date.today()
    bok = g.las_sie(args[0])
    fynd = g.granska(bok, idag)
    open(args[1], "w", encoding="utf-8").write(bygg(bok, fynd, idag, sni))
    print(len(fynd), "fynd")
