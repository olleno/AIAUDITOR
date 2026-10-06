"""Byråsidan /byra/ – white label-erbjudandet med intresseanmälan. Anropas från bygg_sidor.py."""
import os

KROPP = '''<article class="byra"><p class="etikett">För redovisningsbyråer</p>
<h1>AI Auditor i er byrås namn</h1>
<p class="ingress">Låt era kunder granska sin bokföring med er logga, era färger och er kontaktuppgift. I verktyget och rapporten som kunden ser står bara ert namn.</p>
<p class="hand">Det här bygger vi nu</p>
<p>Byråversionen är inte färdig än. Anmäl intresse, så hör vi av oss när den går att prova. Innehåll och pris kan ändras före lansering.</p>

<h2>Det här bygger vi</h2>
<ul class="punkter">
<li><strong>Ert varumärke.</strong> Er logga, era färger och er kontaktuppgift i verktyget och i rapporten. Kunden granskar själv via er länk.</li>
<li><strong>Alla kunder på en gång.</strong> På er egen dator väljer ni flera kunders SIE-filer och får en lista sorterad i rött, gult och grönt – de som behöver ses över först hamnar överst.</li>
<li><strong>Samma granskning som här.</strong> 31 automatiska kontroller av bokföringen, bland annat mot bokföringslagen och momsreglerna, avstämning mot bank, skattekonto, moms och bokslut, och jämförelse med branschen enligt SCB. Ett stöd – det ersätter inte er egen bedömning.</li>
<li><strong>Filerna lämnar aldrig datorn.</strong> SIE-filen läses i webbläsaren och skickas aldrig till någon server. Vi sparar ingen bokföring. Besök räknas anonymt, utan kakor.</li>
</ul>

<h2>Planerat pris</h2>
<div class="tabell"><table><thead><tr><th>Antal kunder</th><th>Pris per månad</th></tr></thead><tbody>
<tr><th scope="row">Upp till 25</th><td>490 kr</td></tr>
<tr><th scope="row">Upp till 100</th><td>990 kr</td></tr>
<tr><th scope="row">Fler än 100</th><td>Offert</td></tr>
</tbody></table></div>
<p class="not">Exklusive moms. Ingen bindningstid.</p>

<section class="cta" id="anmal"><p class="hand">Intresseanmälan</p><h2>Vill ni vara med från start?</h2>
<p>Fyll i det ni vill. När ni trycker på knappen öppnas ett färdigt mejl i ert e-postprogram – inget skickas förrän ni själva skickar det.</p>
<form id="anmalan" class="formular">
<label>Byråns namn<input name="byra" required autocomplete="organization"></label>
<label>Ert namn<input name="namn" autocomplete="name"></label>
<label>E-post<input name="epost" type="email" required autocomplete="email"></label>
<label>Ungefär hur många kunder<select name="antal"><option>Upp till 25</option><option>26–100</option><option>Fler än 100</option></select></label>
<label>Bokföringsprogram ni mest använder<input name="program" placeholder="t.ex. Fortnox, Visma, BL"></label>
<label>Vilket pris vore rimligt för er?<input name="pris"></label>
<label>Något ni vill att vi ska veta<textarea name="ovrigt" rows="3"></textarea></label>
<button class="knapp prim" type="submit">Skicka intresseanmälan</button>
</form>
<p class="not">Eller mejla direkt till <a href="mailto:kansliet@nordwikpartners.se?subject=Intresseanm%C3%A4lan%20AI%20Auditor%20f%C3%B6r%20byr%C3%A5er">kansliet@nordwikpartners.se</a>.</p>
</section>

<h2>Vanliga frågor</h2>
<h3>Vad ser kunden?</h3><p>I verktyget och rapporten ser kunden er logga, era färger och er kontaktuppgift – inget annat namn.</p>
<h3>Måste kunderna ha ett konto?</h3><p>Nej. Kunden öppnar er länk och väljer sin SIE-fil, precis som på aiauditor.se.</p>
<h3>Vilka bokföringsprogram fungerar?</h3><p>Program som kan spara en SIE-fil av typ 4, som är svensk standard. Vi har guider för Fortnox, Spiris, Visma Administration, Bokio, Björn Lundén, Accounted och Briox. <a href="/guider/">Så tar man ut filen</a>.</p>
<h3>Kan vi prova först?</h3><p>Ja. Granskningen på <a href="/#granska">startsidan</a> är densamma och gratis. Testa gärna med en kunds fil redan nu.</p>
</article>
<script>
document.getElementById("anmalan").addEventListener("submit",function(ev){ev.preventDefault();
var f=new FormData(this),rad=function(t,k){return t+": "+(f.get(k)||"")};
var text=["Hej!","","Vi är intresserade av AI Auditor för byråer.","",rad("Byrå","byra"),rad("Namn","namn"),rad("E-post","epost"),rad("Antal kunder","antal"),rad("Bokföringsprogram","program"),rad("Rimligt pris","pris"),"",(f.get("ovrigt")||"")].join("\\n");
if(window.goatcounter&&goatcounter.count)goatcounter.count({path:"byra-intresse",event:true});
location.href="mailto:kansliet@nordwikpartners.se?subject="+encodeURIComponent("Intresseanmälan AI Auditor för byråer – "+(f.get("byra")||""))+"&body="+encodeURIComponent(text);});
</script>'''

FAQ = [("Vad ser kunden?", "I verktyget och rapporten ser kunden byråns logga, färger och kontaktuppgift – inget annat namn."),
       ("Måste kunderna ha ett konto?", "Nej. Kunden öppnar byråns länk och väljer sin SIE-fil."),
       ("Kan vi prova först?", "Ja. Granskningen på aiauditor.se är densamma och gratis.")]


def bygg(sida, brodsmulor, rot):
    smul, ldsmul = brodsmulor([("Start", "/"), ("För byråer", None)])
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    ut = os.path.join(rot, "byra")
    os.makedirs(ut, exist_ok=True)
    open(os.path.join(ut, "index.html"), "w", encoding="utf-8").write(
        sida("AI Auditor för redovisningsbyråer – granskning i er byrås namn",
             "Låt era kunder granska bokföringen med er logga och kontaktuppgift. Översikt över alla kunder i rött, gult och grönt. Från 490 kr i månaden.",
             "/byra/", smul + KROPP, [ldsmul, faq]))
