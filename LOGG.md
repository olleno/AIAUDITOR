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

## 2026-10-06 – Byråsidan och motorn efter 39 riktiga SIE-filer
- /byra/: white label-erbjudande med intresseanmälan (mejl till kansliet@), granskad av Claude (invert), Gemini och GPT. Länkar i meny och sidfot.
- Motorn rättad efter 39 Fortnox-filer: signerade ändringar räknas inte som fel, programbyte räknas inte som sen bokföring, moms under 5 kr hoppas över, omföringar och periodiseringar ger inte momsfel, konto 2610 räknas som utgående moms.

## 2026-10-06 – Lucka-analys mot lag, BFN och Skatteverket, och nattlig regelbevakning
- 16 nya kontroller (BF12, MO13, SK06–SK09, FA01, AV04–AV05, BO06–BO09, AB05–AB07); LO02 tar hänsyn till ungdomsnedsättningen 2026–2027. 51 aktiva kontroller, 47 på SIE-filen. Testbanken 41 av 41.
- Källor kontrollerade av fyra separata genomgångar mot riksdagen.se, Skatteverket, BFN och Srf; granskat av Claude (motsats), Gemini och GPT. Utfall i olleno/granskning/logg.
- Regelbevakningen körs varje natt 02:47 på Kansliets server (Hetzner) för 23 källor och mejlar Olle vid ändring. Gäller både AI Auditor och Kansliets bokförare.
- Sajten ligger kvar på GitHub Pages: ingen kunddata passerar den, gratis och driftsäker.
