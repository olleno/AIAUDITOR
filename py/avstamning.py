"""Lager 2 – avstämning mot handlingar som användaren själv fyller i (inget laddas upp).

handlingar = {
  "bank":   [{"konto": "1930", "datum": "2025-12-31", "saldo": 12345.67}],   # saldo enligt kontoutdraget
  "skattekonto": [{"datum": "2025-12-31", "saldo": -1200.0}],                # enligt Skatteverket: plus = tillgodo, minus = skuld
  "moms":   [{"fran": "2025-01-01", "till": "2025-12-31", "ruta49": 3462}],    # ruta 49: plus = att betala, minus = att få tillbaka
  "bokslut": {"resultat": 10183.0},                                           # årets resultat enligt årsredovisningen (plus = vinst)
}
Returnerar (fynd, rader). rader = avstämningar för rapporten: (regel, vad, enligt handling, enligt bokföring, differens, ok).
"""
from datetime import date

TOL_KR = 1.0          # bank, skattekonto, bokslut: öresavrundning
TOL_MOMS = 3.0        # momsdeklarationen anges i hela kronor per ruta

def _d(s):
    return s if isinstance(s, date) else date.fromisoformat(str(s)[:10])

def _saldo(bok, konto, datum):
    s = bok["ib"].get(konto, 0.0)
    for v in bok["ver"]:
        if v["datum"] and v["datum"] <= datum:
            s += sum(b for k, b in v["rader"] if k == konto)
    return s

def _moms_period(bok, fran, till):
    """Moms att betala (+) / få tillbaka (−) för perioden enligt momskontona 2610–2649,
    utan momsredovisningsverifikationerna (de som för över momsen till 2650)."""
    s = 0.0
    for v in bok["ver"]:
        if not v["datum"] or not (fran <= v["datum"] <= till):
            continue
        if any(k == "2650" for k, _ in v["rader"]):
            continue
        s += sum(b for k, b in v["rader"] if "2610" <= k <= "2649")
    return -s

def _resultat(bok):
    return -sum(b for v in bok["ver"] for k, b in v["rader"] if "3000" <= k <= "8999" and k != "8999")

def avstam(bok, h, lagg):
    """lagg(regel, v, beskr, forslag) är granskarens funktion för att lägga till ett fynd."""
    kr = lambda x: f"{x:,.2f}".replace(",", " ").replace(".", ",")
    rader = []
    for b in (h or {}).get("bank", []) or []:
        konto = str(b.get("konto") or "1930"); dat = _d(b["datum"]); doc = float(b["saldo"])
        bk = _saldo(bok, konto, dat); diff = bk - doc; ok = abs(diff) <= TOL_KR
        rader.append(("BA03", f"Bankens saldo, konto {konto}, {dat}", doc, bk, diff, ok))
        if not ok:
            lagg("BA03", None, f"Konto {konto} visar {kr(bk)} kr den {dat}, men kontoutdraget visar {kr(doc)} kr. Skillnad {kr(diff)} kr.",
                 "Gå igenom kontoutdraget rad för rad mot bokföringen och leta efter saknade, dubbla eller felaktiga belopp.")
    for s in (h or {}).get("skattekonto", []) or []:
        dat = _d(s["datum"]); doc = float(s["saldo"])
        bk = _saldo(bok, "1630", dat); diff = bk - doc; ok = abs(diff) <= TOL_KR
        rader.append(("SK05", f"Skattekontot (1630), {dat}", doc, bk, diff, ok))
        if not ok:
            lagg("SK05", None, f"Konto 1630 visar {kr(bk)} kr den {dat}, men Skatteverkets skattekonto visar {kr(doc)} kr. Skillnad {kr(diff)} kr.",
                 "Hämta skattekontots transaktioner från Skatteverket och bokför det som saknas, till exempel räntor, avgifter eller debiterad skatt.")
    for m in (h or {}).get("moms", []) or []:
        fran, till = _d(m["fran"]), _d(m["till"]); doc = float(m["ruta49"])
        bk = _moms_period(bok, fran, till); diff = bk - doc; ok = abs(diff) <= TOL_MOMS
        rader.append(("MO11", f"Momsdeklaration {fran} – {till}, ruta 49", doc, bk, diff, ok))
        if not ok:
            lagg("MO11", None, f"Momsdeklarationen för {fran} – {till} visar {kr(doc)} kr i ruta 49, men momskontona i bokföringen ger {kr(bk)} kr. Skillnad {kr(diff)} kr.",
                 "Jämför deklarationens rutor med momskontona för perioden. Är deklarationen fel kan den rättas hos Skatteverket; är bokföringen fel rättas den med en rättelseverifikation.")
    bs = (h or {}).get("bokslut") or {}
    if bs.get("resultat") not in (None, ""):
        doc = float(bs["resultat"]); bk = _resultat(bok); diff = bk - doc; ok = abs(diff) <= TOL_KR
        rader.append(("BO01", "Årets resultat enligt årsredovisningen", doc, bk, diff, ok))
        if not ok:
            lagg("BO01", None, f"Årsredovisningen anger årets resultat till {kr(doc)} kr, men bokföringen ger {kr(bk)} kr. Skillnad {kr(diff)} kr.",
                 "Kontrollera om bokslutsposter (avskrivningar, periodiseringar, skatt) saknas i bokföringen eller har ändrats efter bokslutet.")
    return rader
