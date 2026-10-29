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

## 2026-10-14 – Konrad: ihopslagen pristrappa och människorna bakom
- /konrad/ omgjord: pristrappa Gratis 0 / Bevakning 199 (gratis 3 mån) / Pro 399 / Kamrer 2 995 / Ekonomichef 4 995 kr/mån, bokslut 5 995 kr/år, tillvalslista, 20 % av besparing. Kalkylator med totalpris (månad, år, första året).
- Färg bläckblå #1A2A9C (nära Nordea, inte deras #0000A0); grönt valdes bort (för nära Fortnox). Klarspråk, inga AI-säljord.
- "Människorna bakom Konrad": bildbanksbilder från Unsplash (hotlänkade), tydligt märkta "Bildbanksbild · byts ut"; namn och bolagsuppgifter är platshållare tills riktiga finns.
- Villkor: fristgarantin gäller Bevakning–Ekonomichef. Fortfarande noindex. Underlag: Dropbox /Claude/AI-redovisningsbyrå.

## 2026-10-17 – AI-sökpaketet
- JSON-LD: Organization (Kansliet at Nordwik Partners, Foodbergs Stockholm AB, 559518-4457) + WebSite på alla sidor, inklusive startsidan; Dataset med nedladdningslänk på branschsidorna och branschöversikten. Ingen SearchAction (sajten har ingen sökfunktion). Inga betyg.
- Nytt i verktyg/: aiauditor_fakta.py (gemensamma namn, bolagsuppgifter och datum), aiauditor_api.py (öppna JSON-flöden), kontroller_sida.py.
- Ny sida /kontroller/: alla 51 aktiva kontroller med lagrum, direkt ur py/regelkatalog.csv.
- Öppen data (bara läsande, inga personuppgifter): /api/v1/branscher.json, /kontroller.json, /kallor.json och /api/v1/openapi.json. /llms-full.txt med alla kontroller, källor och guider. llms.txt utökad med uppdateringstakt och flödena.
- Svar först: branschsidorna har källa och hämtningsdatum direkt under svaret och rubriker som frågor; branschöversikten inleds med näringslivets median. Guidernas "Senast kontrollerad" är nu ett fast datum (2026-10-08) i stället för byggdatum.
- Datum på alla indexerade sidor. Fabrikskollen: från 869 till 13 fel, alla kända undantag (Konrad, konto och /conrad/ är medvetet noindex; e-postfälten på /konrad/ och /byra/).
- data/ai-fragor.json (46 frågor, 38 med svarssida) och data/ai-synlighet.json (mätprotokoll).
- Tester: tester/aiauditor_test_ai_sok.py. Bygg och testa: `python3 verktyg/bygg_sidor.py && python3 -m unittest discover -s tester -p 'aiauditor_test_*.py'`.
- /conrad/ är en omdirigering till /konrad/ (noindex, kanonisk /konrad/). Konrad hålls utanför llms.txt och flödena tills den släpps.
- Inte publicerat.

## 2026-10-29 – Konrad-sidan: inga löften om automatisk bokföring
- /konrad/: "bokför automatiskt" och "allt automatiskt" ersatta med att Konrad bokför det han är säker på och frågar om resten (mätningen på riktiga böcker 29 okt). Backning: `git revert 4bdfabc`.

## 2026-10-29 – Konrad: EN sajt på aiauditor.se/konrad/ (Olles beslut 29 okt)
- /konrad/ ersatt med det nya innehållet från ~/verket/konrad-sajt (rubriken "Bokföringen är gratis. Du betalar när vi gör jobbet åt dig.", nivåerna och priserna ur data, prisberäknaren, frågorna), i aiauditors mapp. Ny sektion "Det här ingår" (10 funktioner ur funktioner.json, alla märkta "vid lansering"); "Nya avgifter du kanske inte har beställt" märkt "vid lansering".
- Uppdaterat/nytt under /konrad/: villkor/, logga-in/ (inga länkar till appen, märkt "vid lansering"), trygghet/, 312-kalkylator-2026/, vad-kostar-din-bokforing/. Räknarnas JS i konrad/js/, stil i konrad/konrad.css.
- Byggs av verktyg/bygg_konrad.py (anropas av bygg_sidor.py) ur konrad-kalla/ (fragment + data). Alla länkar pekar på /konrad/...; "Granska din bokföring gratis" går till /.
- Ändrat jämfört med konrad-sajt (hårda regler): "Automatisk bokföring" i prislistan -> "Bokföring där Konrad frågar när han är osäker"; samma sak i villkorens punkt om gratisnivån och i jämförelsekalkylatorns text; prisraden om procent av första årets besparing (gamla modellen) borttagen; länkar till guider som inte flyttats (AI-förordningen, kvitton, byta byrå m.fl.) borttagna. Inga priser ändrade.
- Fortfarande noindex, utanför sajtkarta, llms.txt och flöden. Tester: tester/aiauditor_test_konrad.py.
- Backning: `git revert <commit>` (commit-id står i git log: "Konrad: en sajt på aiauditor.se/konrad/").
