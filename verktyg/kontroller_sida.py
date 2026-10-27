"""Sidan /kontroller/: alla aktiva kontroller i AI Auditor med lagrum, direkt ur py/regelkatalog.csv.
Planerade kontroller visas inte (de körs inte än). Anropas från bygg_sidor.py."""
import csv, html, os
import aiauditor_fakta as F

e = html.escape
OMRADEN = ["Grundbokföring", "Moms", "Skatt", "Lön", "Avskrivningar", "Bank och kassa", "Aktiebolag", "Fastighet", "Bokslut"]


def regler(rot):
    with open(os.path.join(rot, "py", "regelkatalog.csv"), encoding="utf-8") as f:
        return [r for r in csv.DictReader(f, delimiter=";") if r["status"] == "aktiv"]


def bygg(sida, brodsmulor, rot):
    rr = regler(rot)
    pa_fil = [r for r in rr if r["lager"] == "1"]
    avst = [r for r in rr if r["lager"] == "2"]
    datum = max(r["senast_kontrollerad"] for r in rr)
    omr = OMRADEN + sorted({r["omrade"] for r in rr} - set(OMRADEN))
    delar = ""
    for o in omr:
        lista = [r for r in rr if r["omrade"] == o]
        if not lista: continue
        rader = "".join(
            f'<tr><th scope="row"><span class="kod">{e(r["id"])}</span> {e(r["regel"])}'
            f'{" <em>(avstämning)</em>" if r["lager"] == "2" else ""}<span class="forkl">{e(r["kontroll"])}</span></th>'
            f'<td>{e(r["kalla"])}</td></tr>' for r in lista)
        delar += (f'<h2 id="{e(o.lower().replace(" ", "-"))}">{e(o)} ({len(lista)})</h2><div class="tabell"><table>'
                  f'<thead><tr><th>Kontroll</th><th>Bygger på</th></tr></thead><tbody>{rader}</tbody></table></div>')
    smul, ldsmul = brodsmulor([("Start", "/"), ("Kontrollerna", None)])
    kropp = (smul + '<article><p class="etikett">Kontrollerna</p><h1>Vad kontrollerar AI Auditor i bokföringen?</h1>'
             f'<p class="ingress">AI Auditor gör {len(rr)} kontroller. {len(pa_fil)} körs direkt på SIE-filen, och {len(avst)} stämmer av bokföringen mot '
             'handlingar som du själv fyller i: kontoutdraget, skattekontot, momsdeklarationerna och årsredovisningen. '
             'Varje kontroll bygger på en lag, ett allmänt råd från Bokföringsnämnden eller Skatteverkets vägledning, som står bredvid.</p>'
             f'<p class="kalla">Källa: AI Auditors regelkatalog, senast kontrollerad mot lagtexterna {datum}. '
             '<a href="/kallor/">Källorna</a> bevakas varje natt. <a href="/api/v1/kontroller.json">Hela katalogen som JSON</a>.</p>'
             + delar +
             '<h2>Är det här en revision?</h2><p>Nej. Kontrollerna letar efter vanliga fel och saker som bör förklaras. '
             'En revision eller ett bokslut gör du med en revisor eller redovisningskonsult. '
             'Kontroller som bygger på god redovisningssed (Rex) är tolkningar, eftersom den standarden inte är öppen för alla.</p>'
             '<aside class="cta"><p class="hand">Nästa steg</p><h2>Kör kontrollerna på din egen bokföring</h2>'
             '<p>Välj SIE-filen från ditt bokföringsprogram. Gratis, och filen lämnar aldrig din dator.</p>'
             '<a class="knapp prim" href="/#granska">Granska bokföringen</a></aside></article>')
    os.makedirs(os.path.join(rot, "kontroller"), exist_ok=True)
    open(os.path.join(rot, "kontroller", "index.html"), "w", encoding="utf-8").write(
        sida("Vad kontrollerar AI Auditor? Alla kontroller med lagrum",
             f"AI Auditors {len(rr)} kontroller av bokföringen: moms, skatt, lön, avskrivningar, bokslut med mera. Varje kontroll med lagrum eller allmänt råd.",
             "/kontroller/", kropp, [ldsmul], publicerad=F.git_datum("verktyg/kontroller_sida.py"), andrad=datum))
    return rr
