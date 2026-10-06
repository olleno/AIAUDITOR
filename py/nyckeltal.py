"""Nyckeltal ur SIE-filen, jämförelse med SCB:s branschnyckeltal och enkla råd.

Nyckeltalen räknas med vanliga definitioner (justerat eget kapital = eget kapital + 79,4 % av
obeskattade reserver). SCB:s egna definitioner kan avvika något – jämförelsen visar läge, inte exakthet.
"""
import json, os
from datetime import date

HÄR = os.path.dirname(os.path.abspath(__file__))
SCB_FIL = os.path.join(HÄR, "data", "branschnyckeltal.json")
SKATT = 0.206

# kod: (namn, scb-kod, enhet, riktning)  riktning: +1 högre är bättre, -1 lägre är bättre, 0 neutralt
NYCKELTAL = {
    "soliditet":   ("Soliditet", "00000340", "%", +1, "Hur stor del av tillgångarna som är egna pengar. Låg soliditet gör bolaget sårbart för förluster."),
    "kassalikv":   ("Kassalikviditet", "00000343", "%", +1, "Pengar och fordringar jämfört med skulder som ska betalas inom ett år. Under 100 % betyder att det kan bli trångt."),
    "rorelsemarg": ("Rörelsemarginal", "0000032G", "%", +1, "Hur mycket av varje intjänad krona som blir kvar efter rörelsens kostnader."),
    "nettomarg":   ("Nettomarginal", "0000032H", "%", +1, "Som rörelsemarginalen, men efter räntor och andra finansiella poster."),
    "bruttomarg":  ("Bruttovinstmarginal", "0000034A", "%", +1, "Försäljning minus varuinköp, i procent av försäljningen."),
    "personal":    ("Personalkostnader / omsättning", "0000033Z", "%", 0, "Hur stor del av omsättningen som går till löner och avgifter."),
    "kundfordr":   ("Kundfordringar / omsättning", "0000035D", "%", -1, "Obetalda kundfakturor i förhållande till årsomsättningen. Högt värde = kunderna betalar sent."),
    "kassa":       ("Kassa och bank / omsättning", "0000035F", "%", 0, "Hur mycket pengar som finns i förhållande till årsomsättningen."),
    "kortfr":      ("Kortfristiga skulder / omsättning", "0000035G", "%", -1, "Skulder som ska betalas inom ett år, i förhållande till årsomsättningen."),
    "avskr":       ("Avskrivningar / omsättning", "00000356", "%", 0, "Hur mycket av omsättningen som motsvaras av värdeminskning på inventarier m.m."),
    "skuldsatt":   ("Skuldsättningsgrad", "0000039C", "ggr", -1, "Skulder delat med justerat eget kapital (eget kapital plus 79,4 % av obeskattade reserver). Högt värde = mycket lånade pengar."),
    "avktot":      ("Avkastning på totalt kapital", "0000031X", "%", +1, "Hur mycket rörelsen tjänar i förhållande till allt kapital i bolaget."),
}

def _sum(saldo, fran, till):
    return sum(v for k, v in saldo.items() if fran <= k[:len(fran)] and k[:len(till)] <= till)

def berakna(bok, idag=None):
    """Returnerar dict med belopp, nyckeltal och periodinfo."""
    saldo = dict(bok["ib"])
    sista = None
    for v in bok["ver"]:
        for k, b in v["rader"]:
            saldo[k] = saldo.get(k, 0) + b
        if v["datum"] and (sista is None or v["datum"] > sista):
            sista = v["datum"]
    start, slut = bok["rar"] if bok["rar"] else (None, None)
    t = sista or slut
    if start and slut:
        t = min(t or slut, slut)          # pågående år: till sista verifikationen; avslutat (även förkortat/förlängt) år: hela perioden
        man = max(1, (t.year - start.year) * 12 + t.month - start.month + 1)
    else:
        man = 12
    helar = 12 / man
    s = lambda a, b: _sum(saldo, a, b)
    oms = -s("30", "37")
    varor = s("40", "49")
    personal = s("70", "76")
    avskr = s("78", "78")
    rorres = -s("3", "7")
    finint = -s("80", "83")
    fin = -s("80", "84")
    resfin = rorres + fin
    arets = -s("3", "8")
    # Skuldkonton (24–29) med debetsaldo är i själva verket fordringar, t.ex. momsfordran på 2650
    deb_skuld = sum(v for k, v in saldo.items() if "24" <= k[:2] <= "29" and v > 0)
    tillg = s("1", "1") + deb_skuld
    obesk = -s("21", "21")
    ek = -s("20", "20") + arets
    justek = ek + (1 - SKATT) * obesk
    kortfr = -s("24", "29") + deb_skuld
    skulder = -s("22", "23") + kortfr + SKATT * obesk
    oms_tillg = s("14", "19") + deb_skuld
    lager = s("14", "14")
    kundf = s("15", "15")
    kassa = s("19", "19")
    aktiekap = -s("2081", "2081")
    omsH = oms * helar
    # Effektiv momssats på försäljningen (för att räkna kundfordringar inkl. moms) – 25 % om den inte går att räkna ut
    utg = -sum(b for v in bok["ver"] for k, b in v["rader"] if k[:3] in ("261", "262", "263") and b < 0)
    momssats = min(0.25, utg / oms) if oms > 0 and utg > 0 else 0.25
    p = lambda a, b: (a / b * 100) if b and abs(b) > 0.5 else None
    nt = {
        "soliditet": p(justek, tillg),
        "kassalikv": p(oms_tillg - lager, kortfr) if kortfr > 1000 else None,
        "rorelsemarg": p(rorres, oms) if oms > 0 else None,
        "nettomarg": p(resfin, oms) if oms > 0 else None,
        "bruttomarg": p(oms - varor, oms) if oms > 0 and varor > 0.5 else None,
        "personal": p(personal, oms) if oms > 0 and personal > 0.5 else None,
        "kundfordr": p(kundf, omsH) if omsH > 0 else None,
        "kassa": p(kassa, omsH) if omsH > 0 else None,
        "kortfr": p(kortfr, omsH) if omsH > 0 else None,
        "avskr": p(avskr, oms) if oms > 0 and avskr > 0.5 else None,
        "skuldsatt": (skulder / justek) if justek > 0.5 else None,
        "avktot": p((rorres + finint) * helar, tillg),
    }
    belopp = dict(oms=oms, omsH=omsH, varor=varor, personal=personal, avskr=avskr, rorres=rorres, resfin=resfin,
                  arets=arets, tillg=tillg, ek=ek, justek=justek, skulder=skulder, kortfr=kortfr, kundf=kundf,
                  kassa=kassa, aktiekap=aktiekap, momssats=momssats, skattekonto=s("1630", "1630"), kostnader=s("4", "7"))
    return {"nt": nt, "belopp": belopp, "manader": man, "sista": sista, "delar": man < 12}

def _storlek(personal_helar):
    # Antal anställda finns inte i SIE-filen – grov uppskattning från personalkostnaden (ca 600 000 kr/anställd och år inkl. avgifter)
    if personal_helar < 50_000: return "001"
    n = personal_helar / 600_000
    for gr, kod in ((4.5, "1-4"), (9.5, "5-9"), (19.5, "10-19"), (49.5, "20-49"), (99.5, "50-99"), (199.5, "100-199"), (499.5, "200-499")):
        if n < gr: return kod
    return "+500"

def jamfor(berak, sni, storlek=None, minsta_antal=30):
    """Jämför med SCB. Faller tillbaka till bredare bransch eller storlek om underlaget är litet."""
    if not os.path.exists(SCB_FIL) or not sni:
        return None
    scb = json.load(open(SCB_FIL, encoding="utf-8"))
    st = storlek or _storlek(berak["belopp"]["personal"] * (12 / berak["manader"]))
    koder = []
    k = sni
    while k:
        koder.append(k)
        k = k[:-1].rstrip(".") if len(k) > 2 else ""
    val = None
    for kod in koder:
        for s in (st, "TOT"):
            d = scb["data"].get(kod, {}).get(s)
            if d and (d.get("0000028K", [0])[1] or 0) >= minsta_antal:
                val = (kod, s, d); break
        if val: break
    if not val:
        return None
    kod, s, d = val
    rader = []
    for nyc, (namn, scbkod, enhet, rikt, forkl) in NYCKELTAL.items():
        v = berak["nt"].get(nyc)
        q = d.get(scbkod)
        if v is None or not q or None in q:
            continue
        uk, med, ok = sorted(q)
        if uk == ok:      # hela branschen på samma värde – säger inget
            continue
        if v < uk: lage = 0
        elif v < med: lage = 1
        elif v <= ok: lage = 2
        else: lage = 3
        if rikt == 0: bed = "neutral"
        elif (lage == 3 and rikt > 0) or (lage == 0 and rikt < 0): bed = "bra"
        elif (lage == 0 and rikt > 0) or (lage == 3 and rikt < 0): bed = "svag"
        else: bed = "normal"
        rader.append(dict(id=nyc, namn=namn, enhet=enhet, varde=v, uk=uk, med=med, ok=ok, lage=lage, bed=bed, forkl=forkl))
    return {"sni": kod, "sni_text": scb["sni"].get(kod, kod), "storlek": s, "storlek_text": scb["storlek"].get(s, s),
            "uppskattad_storlek": storlek is None, "antal": int(d["0000028K"][1]), "ar": scb["ar"], "kalla": scb["kalla"], "rader": rader}

def rad(berak, jmf=None):
    """Enkla råd. Returnerar lista av (rubrik, text)."""
    b, nt, ut = berak["belopp"], berak["nt"], []
    kr0 = lambda x: f"{x:,.0f}".replace(",", " ")
    if b["kundf"] > 1000 and b["omsH"] > 0:
        dagar = b["kundf"] / (b["omsH"] * (1 + b["momssats"])) * 365   # kundfordringar inkl. moms mot omsättning inkl. moms
        if dagar > 30:
            ut.append(("Kunderna betalar sent",
                       f"Obetalda kundfakturor på {kr0(b['kundf'])} kr motsvarar ungefär {dagar:.0f} dagars försäljning. "
                       "Skicka påminnelse dagen efter förfallodagen, fakturera direkt efter leverans och överväg kortare betalvillkor, till exempel 15 dagar."))
    if nt["kassalikv"] is not None and nt["kassalikv"] < 100 and b["kortfr"] > 1000:
        ut.append(("Risk för likviditetsbrist",
                   f"Skulder som ska betalas inom ett år ({kr0(b['kortfr'])} kr) är större än pengar och fordringar. "
                   "Gör en enkel plan över in- och utbetalningar de närmaste tre månaderna och prioritera skatter och moms."))
    if b["rorres"] < -1000:
        ut.append(("Rörelsen går med förlust",
                   f"Rörelseresultatet är {kr0(b['rorres'])} kr för perioden. Gå igenom de största kostnaderna och se om något kan sägas upp eller förhandlas, "
                   "och om priserna täcker kostnaderna."))
    if b["skattekonto"] < -1000:
        ut.append(("Skuld på skattekontot",
                   f"Bokföringen visar en skuld på skattekontot på {kr0(-b['skattekonto'])} kr. Betala in den för att slippa kostnadsränta, "
                   "och kontrollera mot Skatteverkets saldo."))
    man_kost = b["kostnader"] / berak["manader"] if berak["manader"] else 0
    if man_kost > 0 and b["kassa"] > 12 * man_kost and b["kassa"] > 100_000:
        ut.append(("Pengar som står still",
                   f"Kassa och bank ({kr0(b['kassa'])} kr) räcker till mer än ett års kostnader. Överväg att flytta en del till ett sparkonto med ränta."))
    if jmf:
        for r in jmf["rader"]:
            if r["bed"] == "svag" and r["id"] not in ("kassalikv", "kundfordr"):
                ut.append((f"{r['namn']} sämre än de flesta i branschen",
                           f"{r['namn']} är {r['varde']:.1f} {r['enhet']}, sämre än tre av fyra jämförbara företag ({jmf['sni_text'].lower()}). {r['forkl']}"))
    if berak["delar"] and ut:
        ut.append(("Obs: året pågår", f"Bokföringen omfattar {berak['manader']} månader. Säsongsvariationer kan göra att bilden ändras till årets slut."))
    return ut
