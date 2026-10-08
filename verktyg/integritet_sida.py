"""Sidan /integritet/: vem som står bakom AI Auditor och vad som händer med uppgifterna."""
import os

KROPP = '''<article class="byra"><p class="etikett">Integritet och trygghet</p>
<h1>Din bokföring lämnar aldrig din dator</h1>
<p class="ingress">AI Auditor granskar SIE-filen i din egen webbläsare. Filen skickas inte till oss eller till någon annan, och vi kan inte se den. Stänger du fliken är den borta. Vill du spara resultatet kan du skapa ett frivilligt konto – då sparas bara en sammanfattning.</p>

<h2>Vem står bakom</h2>
<p>AI Auditor drivs av Kansliet at Nordwik Partners. Frågor och synpunkter: <a href="mailto:kansliet@nordwikpartners.se">kansliet@nordwikpartners.se</a>.</p>

<h2>Vad som händer med uppgifterna</h2>
<div class="tabell"><table><thead><tr><th>Uppgift</th><th>Vart den tar vägen</th></tr></thead><tbody>
<tr><th scope="row">SIE-filen och allt i den</th><td class="fa">Läses och granskas i din webbläsare. Skickas ingenstans och sparas inte.</td></tr>
<tr><th scope="row">Saldon du skriver in för avstämningen</th><td class="fa">Samma sak – används bara i din webbläsare.</td></tr>
<tr><th scope="row">Rapporten</th><td class="fa">Skapas i din webbläsare. Du väljer själv om du skriver ut den, sparar den eller skickar den vidare.</td></tr>
<tr><th scope="row">"Fördjupa med din egen AI"</th><td class="fa">Texten kopieras till ditt urklipp. Du väljer själv om och var du klistrar in den; då gäller den AI-tjänstens villkor.</td></tr>
<tr><th scope="row">Besöksstatistik</th><td class="fa">GoatCounter räknar sidvisningar och knapptryck (till exempel att en granskning startades) utan kakor och utan att känna igen dig. Inget innehåll ur filen räknas.</td></tr>
<tr><th scope="row">Själva webbsidan</th><td class="fa">Levereras av GitHub Pages. Som alla webbservrar ser den din IP-adress när sidan hämtas. Granskningsprogrammet och typsnitten ligger på samma ställe – inget hämtas från Google.</td></tr>
<tr><th scope="row">Hämta från Fortnox (frivilligt)</th><td class="fa">Bara om du väljer det i stället för att ladda upp en fil. Du godkänner i Fortnox att vi får läsa bokföringen för senaste räkenskapsåret. Den hämtas till Kansliets server hos Hetzner i Tyskland, görs om till en SIE-fil och lämnas till din webbläsare, som granskar den som vanligt. Inget skrivs till disk: filen finns i serverns minne tills din webbläsare har hämtat den, högst tio minuter, och behörigheten i Fortnox återkallas direkt. Vi kan inte ändra något i Fortnox.</td></tr>
<tr><th scope="row">Konto (frivilligt)</th><td class="fa">Bara om du själv skapar ett: din e-postadress och de sammanfattningar du väljer att spara – bolagets namn och organisationsnummer, perioden, några nyckeltal och vilka kontroller som gav anmärkning. Aldrig filen eller verifikationerna. Lagras på Kansliets server hos Hetzner i Tyskland. Du kan ta bort enskilda granskningar eller hela kontot när du vill.</td></tr>
<tr><th scope="row">Mejl och intresseanmälan</th><td class="fa">Öppnar ditt eget e-postprogram. Det du skickar används bara för att svara dig.</td></tr>
</tbody></table></div>

<h2>Vanliga frågor</h2>
<h3>Används min bokföring för att träna AI?</h3><p>Nej. Laddar du upp en fil når den oss aldrig, inte heller om du har ett konto. Hämtar du från Fortnox passerar den servern i några sekunder utan att sparas. Granskningen är fasta regler med lagrum, inte en AI-modell som lär sig av ditt material.</p>
<h3>Behövs ett personuppgiftsbiträdesavtal?</h3><p>Inte när du laddar upp en fil, eftersom vi då inte behandlar bokföringen eller personuppgifterna i den. Hämtar du från Fortnox behandlar vi den kort för att göra om den till en fil – vill ni ha ett biträdesavtal för det, skriv till kansliet@nordwikpartners.se. Med ett konto behandlar vi din e-postadress för att kunna logga in dig och, om du vill, påminna dig varje kvartal – inget annat.</p>
<h3>Använder sajten kakor?</h3><p>Nej. Loggar du in på ditt konto sparas en inloggningsnyckel i din webbläsare, så att du slipper logga in varje gång. Den tas bort när du loggar ut.</p>
<h3>Måste jag skapa ett konto?</h3><p>Nej. Granskningen fungerar likadant utan konto. Kontot behövs bara om du vill spara resultatet och jämföra med nästa granskning.</p>
<h3>Hur kan jag kontrollera att filen inte skickas?</h3><p>Granska exempelfilen först, så att programmet laddas. Koppla sedan från internet och välj din egen fil. Granskningen fungerar ändå – det går bara om allt sker på din dator.</p>
<h3>Vilka regler bygger granskningen på?</h3><p>Lagar, Bokföringsnämndens allmänna råd och Skatteverkets vägledning. <a href="/kallor/">Se alla källor</a>, som kontrolleras varje natt.</p>
</article>'''

def bygg(sida, brodsmulor, rot):
    smul, ldsmul = brodsmulor([("Start", "/"), ("Integritet", None)])
    os.makedirs(os.path.join(rot, "integritet"), exist_ok=True)
    open(os.path.join(rot, "integritet", "index.html"), "w", encoding="utf-8").write(
        sida("Integritet – din bokföring lämnar aldrig din dator", "AI Auditor granskar SIE-filen i din webbläsare. Inget skickas, inget sparas, inga kakor. Vem som står bakom och vad som händer med uppgifterna.",
             "/integritet/", smul + KROPP, [ldsmul]))
