"""Maskinläsbar data för AI-tjänster och agenter: statiska, bara läsande JSON-filer under /api/v1/,
en OpenAPI-beskrivning och /llms-full.txt. Anropas från bygg_sidor.py, så flödena alltid stämmer med sidorna.

Inga personuppgifter: bara SCB:s branschstatistik, regelkatalogen och källförteckningen."""
import csv, json, os, re, unicodedata
import aiauditor_fakta as F

LICENS_SCB = "https://creativecommons.org/publicdomain/zero/1.0/"


def _nyckel(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def _skriv(rot, namn, data):
    p = os.path.join(rot, namn)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1 if "openapi" in namn else None, separators=None if "openapi" in namn else (",", ":"))
        f.write("\n")


def branscher(scb, sidor, visa, enhet):
    kalla = f"SCB, Företagens ekonomi (tabell BNTT01), år {scb['ar']}"
    ut = []
    for k, s in sidor.items():
        tot = scb["data"][k]["TOT"]
        n = tot.get("0000028K")
        nt = {}
        for kod, kort, _ in visa:
            v = tot.get(kod)
            if not v or all(x is None for x in v): continue
            nt[_nyckel(kort)] = {"namn": kort, "enhet": enhet.get(kod, " %").strip(),
                                 "undre_kvartil": v[0], "median": v[1], "ovre_kvartil": v[2]}
        ut.append({"sni": k, "namn": scb["sni"][k], "url": f"{F.SAJT}/bransch/{s}/",
                   "antal_foretag": int(n[1]) if n and n[1] is not None else None, "ar": int(scb["ar"]),
                   "nyckeltal": nt, "kalla": kalla, "hamtad": F.SCB_HAMTAD})
    return {"titel": "Branschnyckeltal per SNI-bransch", "utgivare": F.NAMN, "kalla": kalla, "kalla_url": "https://www.scb.se",
            "licens": LICENS_SCB, "hamtad": F.SCB_HAMTAD, "ar": int(scb["ar"]), "antal": len(ut),
            "anmarkning": "Kvartilerna anges som SCB redovisar dem. Branscher med färre än 30 företag, eller samma siffror som huvudbranschen, ingår inte.",
            "branscher": ut}


def kontroller(rot):
    with open(os.path.join(rot, "py", "regelkatalog.csv"), encoding="utf-8") as f:
        rr = [r for r in csv.DictReader(f, delimiter=";") if r["status"] == "aktiv"]
    ut = [{"id": r["id"], "omrade": r["omrade"], "regel": r["regel"], "kontroll": r["kontroll"],
           "del": "SIE-filen" if r["lager"] == "1" else "avstämning mot handlingar",
           "kalla": r["kalla"], "senast_kontrollerad": r["senast_kontrollerad"],
           "url": f"{F.SAJT}/kontroller/#{r['omrade'].lower().replace(' ', '-')}"} for r in rr]
    return {"titel": "AI Auditors aktiva kontroller", "utgivare": F.NAMN, "antal": len(ut),
            "senast_kontrollerad": max(r["senast_kontrollerad"] for r in ut),
            "anmarkning": "Varje kontroll bygger på lag, Bokföringsnämndens allmänna råd eller Skatteverkets vägledning (fältet kalla). Planerade kontroller ingår inte.",
            "kontroller": ut}


def kallor():
    d = json.load(open(os.path.join(os.path.dirname(__file__), "kallor.json"), encoding="utf-8"))
    ut = [{"id": x["id"], "namn": x["namn"], "typ": x["typ"], "url": x["url"], "kontroller": x["regler"],
           "bevakas": "varje natt", "uppdaterad": F.KALLOR_UPPDATERAD} for x in d["kallor"] if "aiauditor" in x["galler"]]
    return {"titel": "Källor som AI Auditors kontroller bygger på", "utgivare": F.NAMN, "antal": len(ut),
            "uppdaterad": F.KALLOR_UPPDATERAD, "kallor": ut}


def _obj(req, props):
    return {"type": "object", "required": req, "properties": props}


S, I, N = {"type": "string"}, {"type": "integer"}, {"type": ["number", "null"]}
DATUM = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}
SCHEMAN = {
    "Branscher": _obj(["kalla", "hamtad", "ar", "antal", "branscher"], {
        "kalla": S, "kalla_url": S, "licens": S, "hamtad": DATUM, "ar": I, "antal": I,
        "branscher": {"type": "array", "items": _obj(["sni", "namn", "url", "nyckeltal", "kalla", "hamtad"], {
            "sni": S, "namn": S, "url": S, "antal_foretag": {"type": ["integer", "null"]}, "ar": I, "kalla": S, "hamtad": DATUM,
            "nyckeltal": {"type": "object", "additionalProperties": _obj(["namn", "enhet", "median"], {
                "namn": S, "enhet": S, "undre_kvartil": N, "median": N, "ovre_kvartil": N})}})}}),
    "Kontroller": _obj(["antal", "senast_kontrollerad", "kontroller"], {
        "antal": I, "senast_kontrollerad": DATUM,
        "kontroller": {"type": "array", "items": _obj(["id", "omrade", "regel", "kontroll", "del", "kalla", "senast_kontrollerad"], {
            "id": S, "omrade": S, "regel": S, "kontroll": S, "del": {"type": "string", "enum": ["SIE-filen", "avstämning mot handlingar"]},
            "kalla": S, "senast_kontrollerad": DATUM, "url": S})}}),
    "Kallor": _obj(["antal", "uppdaterad", "kallor"], {
        "antal": I, "uppdaterad": DATUM,
        "kallor": {"type": "array", "items": _obj(["id", "namn", "typ", "url", "kontroller", "uppdaterad"], {
            "id": S, "namn": S, "typ": S, "url": S, "kontroller": S, "bevakas": S, "uppdaterad": DATUM})}}),
}
VAGAR = {"/branscher.json": ("Branscher", "Branschnyckeltal (kvartiler) från SCB för alla branscher som har en sida på aiauditor.se"),
         "/kontroller.json": ("Kontroller", "Alla aktiva kontroller med lagrum"),
         "/kallor.json": ("Kallor", "Lagar och myndighetssidor som kontrollerna bygger på")}


def openapi():
    return {"openapi": "3.1.0",
            "info": {"title": f"{F.NAMN} – öppen data", "version": "1.0.0",
                     "description": "Statiska, bara läsande JSON-filer. Ingen inloggning, inga personuppgifter, inga anrop som ändrar något. "
                                    "Själva bokföringsgranskningen körs bara i användarens webbläsare och har inget API.",
                     "contact": {"name": F.AVSANDARE, "email": F.EPOST}},
            "servers": [{"url": F.SAJT + "/api/v1"}],
            "paths": {v: {"get": {"summary": t, "operationId": n[0].lower() + n[1:],
                                  "responses": {"200": {"description": t, "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{n}"}}}}}}}
                      for v, (n, t) in VAGAR.items()},
            "components": {"schemas": SCHEMAN}}


def llms_full(kon, kal, guider, n_branscher, ar):
    r = [f"# {F.NAMN} – fullständig text för AI-tjänster", "",
         f"> {F.BESKRIVNING}", "",
         f"{F.NAMN} drivs av {F.AVSANDARE} (bifirma till {F.BOLAG}, org.nr {F.ORGNR}). Kontakt: {F.EPOST}.",
         "Granskningen körs helt i användarens webbläsare: SIE-filen skickas ingenstans och sparas inte. Sajten har inga annonslänkar.", "",
         "Kortversion: https://aiauditor.se/llms.txt. Öppen data: https://aiauditor.se/api/v1/openapi.json", "",
         f"## Kontrollerna ({kon['antal']} st, senast kontrollerade mot lagtexterna {kon['senast_kontrollerad']})", ""]
    omr = []
    for k in kon["kontroller"]:
        if k["omrade"] not in omr: omr.append(k["omrade"])
    for o in omr:
        r += [f"### {o}", ""]
        r += [f"- {k['id']} {k['regel']}{' (avstämning mot handlingar)' if k['del'] != 'SIE-filen' else ''}: {k['kontroll']}. Bygger på: {k['kalla']}."
              for k in kon["kontroller"] if k["omrade"] == o]
        r.append("")
    r += [f"## Källor ({kal['antal']} st, bevakas varje natt, förteckningen uppdaterad {kal['uppdaterad']})", ""]
    r += [f"- {x['namn']} ({x['url']}): kontroller {x['kontroller']}" for x in kal["kallor"]]
    r += ["", f"## Så tar du ut en SIE-fil (menyvägarna kontrollerade {F.GUIDER_KONTROLLERAD})", ""]
    for g in guider:
        r += [f"### {re.sub('<[^>]+>', '', g['namn'])} (https://aiauditor.se/guider/{g['slug']}/)", ""]
        r += [f"{i + 1}. {re.sub('<[^>]+>', '', s)}" for i, s in enumerate(g["steg"])]
        r += [f"Källa: {t} ({u})" for t, u in g["kallor"]] + [""]
    r += ["## Branschnyckeltal", "",
          f"{n_branscher} branscher (SNI 2007) med soliditet, kassalikviditet, rörelsemarginal, nettomarginal med mera, som undre kvartil, median och övre kvartil.",
          f"Källa: SCB, Företagens ekonomi (tabell BNTT01), år {ar}, hämtad {F.SCB_HAMTAD}, licens CC0. Visas obearbetade.",
          "Alla siffror: https://aiauditor.se/api/v1/branscher.json. En sida per bransch under https://aiauditor.se/bransch/.", ""]
    return "\n".join(r)


def bygg(rot, scb, sidor, visa, enhet, guider):
    b, kon, kal = branscher(scb, sidor, visa, enhet), kontroller(rot), kallor()
    _skriv(rot, "api/v1/branscher.json", b)
    _skriv(rot, "api/v1/kontroller.json", kon)
    _skriv(rot, "api/v1/kallor.json", kal)
    _skriv(rot, "api/v1/openapi.json", openapi())
    with open(os.path.join(rot, "llms-full.txt"), "w", encoding="utf-8") as f:
        f.write(llms_full(kon, kal, guider, len(sidor), scb["ar"]))
