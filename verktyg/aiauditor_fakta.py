"""Gemensamma uppgifter om AI Auditor: samma namn, beskrivning och avsändare på sajten, i llms.txt,
i JSON-LD (Organization/WebSite) och i API-flödena. Ändra här, inte på flera ställen.

Bolagsuppgifterna är desamma som på nordwikpartners.se (Foodbergs Stockholm AB, org.nr 559518-4457)."""

SAJT = "https://aiauditor.se"
NAMN = "AI Auditor"
BESKRIVNING = ("Gratis granskning av bokföring i SIE-format mot bokföringslagen, momslagen och skattereglerna, "
               "med jämförelse mot SCB:s branschnyckeltal. Körs i webbläsaren.")
AVSANDARE = "Kansliet at Nordwik Partners"
BOLAG = "Foodbergs Stockholm AB"
ORGNR = "559518-4457"
EPOST = "kansliet@nordwikpartners.se"
AVSANDARE_URL = "https://nordwikpartners.se/"

# Datum då innehållet senast ändrades eller kontrollerades (inte byggdatum – bygget får inte påstå nya kontroller).
SCB_HAMTAD = "2026-10-06"          # branschnyckeltal.json hämtad från SCB (BNTT01)
GUIDER_KONTROLLERAD = "2026-10-08"  # menyvägarna kontrollerade mot leverantörernas hjälpsidor
KALLOR_UPPDATERAD = "2026-10-06"    # förteckningen i kallor.json och regelkatalog.csv
BYRA_UPPDATERAD = "2026-10-06"
INTEGRITET_UPPDATERAD = "2026-10-13"

import os, subprocess

_ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git_datum(fil, forsta=True):
    """Datum (ÅÅÅÅ-MM-DD) för källfilens första (publicerad) eller senaste (ändrad) commit. Aldrig dagens datum."""
    ut = subprocess.run(["git", "log", "--follow", "--format=%as", "--", fil], cwd=_ROT, capture_output=True, text=True, check=True).stdout.split()
    if not ut:
        raise RuntimeError(f"{fil}: ingen git-historik, så publiceringsdatum kan inte fastställas")
    return ut[-1] if forsta else ut[0]


ORG = {"@type": "Organization", "@id": SAJT + "/#organisation", "name": AVSANDARE, "legalName": BOLAG,
       "taxID": ORGNR, "email": EPOST, "url": AVSANDARE_URL}
WEBBPLATS = {"@type": "WebSite", "@id": SAJT + "/#webbplats", "name": NAMN, "url": SAJT + "/", "inLanguage": "sv",
             "description": BESKRIVNING, "publisher": {"@id": SAJT + "/#organisation"}}


def org_ld():
    """Organization + WebSite som ett JSON-LD-block. Ingen SearchAction: sajten har ingen sökfunktion."""
    return {"@context": "https://schema.org", "@graph": [ORG, WEBBPLATS]}
