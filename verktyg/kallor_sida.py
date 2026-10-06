"""Sidan /kallor/: alla källor som AI Auditors kontroller bygger på och som kontrolleras varje natt."""
import json, os, html
e = html.escape

def bygg(sida, brodsmulor, rot):
    d = json.load(open(os.path.join(os.path.dirname(__file__), "kallor.json"), encoding="utf-8"))
    k = [x for x in d["kallor"] if "aiauditor" in x["galler"]]
    lagar = "".join(f'<li><a href="{e(x["url"])}" rel="nofollow noopener">{e(x["namn"])}</a><span class="forkl">Kontroller: {e(x["regler"])}</span></li>' for x in k if x["typ"] == "lag")
    sidor = "".join(f'<li><a href="{e(x["url"])}" rel="nofollow noopener">{e(x["namn"])}</a><span class="forkl">Kontroller: {e(x["regler"])}</span></li>' for x in k if x["typ"] != "lag")
    smul, ldsmul = brodsmulor([("Start", "/"), ("Källor", None)])
    kropp = (smul + '<article><p class="etikett">Källor</p><h1>Källorna bakom granskningen</h1>'
             f'<p class="ingress">Varje kontroll i AI Auditor bygger på en lag, ett allmänt råd från Bokföringsnämnden eller Skatteverkets vägledning. De {len(k)} källorna nedan kontrolleras varje natt. Ändras en lag eller ett belopp går vi igenom kontrollerna innan granskningen uppdateras – inget ändras automatiskt.</p>'
             f'<h2>Lagar</h2><p>För lagarna kontrolleras vilken ändring (SFS-nummer) riksdagens text är uppdaterad till.</p><ul class="lankar stora">{lagar}</ul>'
             f'<h2>Myndigheternas vägledning</h2><p>Här jämförs sidans text med föregående natt.</p><ul class="lankar stora">{sidor}</ul>'
             '<h2>Det som inte bevakas automatiskt</h2><p>Srf konsulternas och FAR:s standard för redovisningsuppdrag (Rex) är inte öppen för alla. Kontroller som bygger på den är märkta som tolkning av god redovisningssed.</p></article>')
    os.makedirs(os.path.join(rot, "kallor"), exist_ok=True)
    open(os.path.join(rot, "kallor", "index.html"), "w", encoding="utf-8").write(
        sida("Källor – lagar och regler bakom AI Auditor", f"De {len(k)} lagar och myndighetssidor som AI Auditors kontroller bygger på, kontrollerade varje natt.", "/kallor/", kropp, [ldsmul]))
