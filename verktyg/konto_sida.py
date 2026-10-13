"""Sidan /konto/: frivilligt konto med sparade granskningar och jämförelser."""
import os
KROPP = '''<article><p class="etikett">Mitt konto</p><h1>Dina sparade granskningar</h1>
<p class="ingress">Här ser du sammanfattningarna du har sparat och vad som har ändrats mellan granskningarna. Själva bokföringen sparas aldrig.</p>
<div id="kontorot"><p class="spara-status">Laddar…</p></div></article>
<script src="/konto.js"></script><script>window.aiaKonto && window.aiaKonto.kontosida(document.getElementById("kontorot"));</script>'''
def bygg(sida, brodsmulor, rot):
    smul, ldsmul = brodsmulor([("Start", "/"), ("Mitt konto", None)])
    os.makedirs(os.path.join(rot, "konto"), exist_ok=True)
    html = sida("Mitt konto – AI Auditor", "Sparade granskningar och jämförelse mot förra gången.", "/konto/", smul + KROPP, [ldsmul])
    html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)
    open(os.path.join(rot, "konto", "index.html"), "w", encoding="utf-8").write(html)
