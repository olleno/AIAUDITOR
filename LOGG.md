# AI Auditor – logg

## 2026-10-06
- Sajten publicerad på https://aiauditor.se via GitHub Pages (repo olleno/AIAUDITOR, gren main, rot). Domän hos Loopia.
- DNS hos Loopia: aiauditor.se → GitHubs fyra adresser (185.199.108–111.153), www → CNAME olleno.github.io. Parkeringsposterna för www borttagna. Jokerposten (*) pekar fortfarande på Loopias parkering.
- Besöksmätning: GoatCounter, egen sajt https://aiauditor.goatcounter.com (i kontot nordwik). Händelser som räknas: granskning-egen-fil, granskning-exempel, granskning-fel, kopiera-ai-underlag, kopiera-byratext, vy-sjalv/byra/revisor.
- Google Search Console: egendom https://aiauditor.se/ verifierad med filen googlebc549f95fdfa689d.html (får inte tas bort). Sajtkarta inskickad.
- Bing Webmaster Tools: aiauditor.se tillagd, verifierad med meta-taggen msvalidate.01. Sajtkarta inskickad.
- SEO: titel, beskrivning, kanonisk adress, delningsbild (bilder/delning.jpg), strukturerad data (WebApplication + FAQPage).
- Texterna granskade av Gemini och GPT (logg i olleno/granskning).
- Bilder: Unsplash (skrivbord, Cht Gsml) och Pexels (papper, pärmar) – fria licenser.
- Branschsidor: 851 sidor under /bransch/ från SCB:s branschnyckeltal (BNTT01, 2024), byggda med verktyg/bygg_sidor.py. Branscher med färre än 30 företag, eller samma siffror som huvudbranschen, får ingen egen sida. SCB:s siffror visas obearbetade med "Källa: SCB" (CC0).
- Guider: 7 guider under /guider/ för SIE-export (Fortnox, Spiris, Visma Administration, Bokio, Björn Lundén, Accounted, Briox). Menyvägar från leverantörernas hjälpsidor (källor på varje sida). PE Accounting/Kleer utelämnad – ingen offentlig instruktion hittades. Granskade av Gemini (inga invändningar) och GPT (invändningar avfärdade mot källorna).
- Avstämning mot handlingar (lager 2): användaren fyller i bankens saldo, skattekontots saldo, momsdeklarationernas ruta 49 och årets resultat enligt årsredovisningen. Regler MO11, SK05, BA03, BO01 aktiverade. Körs i webbläsaren; inget skickas.
- Startsidan läser ?sni= från branschsidorna och fyller i branschen.
- Uppföljning: GitHubs DNS-kontroll godkänd efter omsparad domän; "Enforce HTTPS" påslagen (http skickas nu till https). Sajtkartan inskickad igen i Google Search Console efter branschsidorna (861 adresser). Startsidan och exempelgranskningen kontrollerade live.
