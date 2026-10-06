"""Granskaren v2 – lager 1 (fasta regler på SIE4-fil).

Varje fynd har ett regel-id ur regelkatalog.csv. Rubrik, källa och allvar hämtas ur katalogen,
så att paragrafhänvisningar aldrig skrivs i koden.

Användning:  python3 -I granskaren.py bokforing.se rapport.html [ÅÅÅÅ-MM-DD]
(datumet är "idag" – styr vad som räknas som avslutat år; standard är dagens datum)
"""
import csv, html, os, re, shlex, sys
from collections import Counter, defaultdict
from datetime import date

HÄR = os.path.dirname(os.path.abspath(__file__))
KATALOG = {r["id"]: r for r in csv.DictReader(open(os.path.join(HÄR, "regelkatalog.csv"), encoding="utf-8"), delimiter=";")}

# ---------- Läsa SIE ----------
def _tolka(rad):
    rad = rad.replace("{", " { ").replace("}", " } ")
    try:
        return shlex.split(rad, posix=True)
    except ValueError:
        return rad.split()

def _datum(s):
    s = s.strip()
    if not re.fullmatch(r"\d{8}", s):
        return None
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))

def las_sie(sokvag):
    raw = open(sokvag, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp437")
    bok = {"namn": "", "orgnr": "", "rar": None, "konton": {}, "ib": defaultdict(float),
           "ub": {}, "har_ib": False, "ver": []}
    akt = None
    for rad in text.splitlines():
        rad = rad.strip()
        if rad == "}":
            akt = None
            continue
        if not rad.startswith("#"):
            continue
        f = _tolka(rad)
        if not f:
            continue
        t = f[0].upper()
        if t == "#FNAMN":
            bok["namn"] = f[1]
        elif t == "#ORGNR":
            bok["orgnr"] = f[1]
        elif t == "#RAR" and f[1] == "0":
            bok["rar"] = (_datum(f[2]), _datum(f[3]))
        elif t == "#KONTO":
            bok["konton"][f[1]] = f[2] if len(f) > 2 else ""
        elif t == "#IB" and f[1] == "0":
            bok["ib"][f[2]] += float(f[3]); bok["har_ib"] = True
        elif t == "#UB" and f[1] == "0":
            bok["ub"][f[2]] = float(f[3])
        elif t == "#VER":
            akt = {"serie": f[1], "nr": int(f[2]) if f[2].isdigit() else f[2], "datum": _datum(f[3]),
                   "text": f[4] if len(f) > 4 else "", "regdatum": _datum(f[5]) if len(f) > 5 else None,
                   "rader": [], "andrade": 0}
            bok["ver"].append(akt)
        elif t == "#TRANS" and akt is not None:
            i = f.index("}") + 1
            akt["rader"].append((f[1], float(f[i])))
        elif t in ("#RTRANS", "#BTRANS") and akt is not None:
            # tillagd/borttagen rad – påverkar inte saldot (#RTRANS följs av en #TRANS).
            # Har raden en signatur (vem som ändrade) är ändringen dokumenterad, som BFL kräver.
            i = f.index("}") + 1
            if len(f) > i + 4 and f[i + 4].strip():
                akt["andrade_sign"] = akt.get("andrade_sign", 0) + 1
            else:
                akt["andrade"] += 1
    return bok

# ---------- Hjälp ----------
MOMSSATSER = (0.25, 0.12, 0.06)
EJ_AVDRAG = {"6072", "6992", "7632"}
MOMSFRIA_FORS = {"3004", "3044", "3045", "3048", "3054", "3055", "3058", "3100", "3105", "3108", "3305", "3308"}
PRIVATA_ORD = ["systembolaget", "ikea", "apotek", "netflix", "spotify", "privat", "semester",
               "zalando", "h&m", "barnkläder", "blommor", "gym"]
PBB = {2024: 57300, 2025: 58800, 2026: 59200}           # prisbasbelopp
STATSLANERANTA = {2025: 0.0196, 2026: 0.0255}           # schablonintäkt periodiseringsfond (statslåneräntan 30 nov året före)
UNGA_AVGIFT = (date(2026, 4, 1), date(2027, 9, 30), 0.2081)   # nedsatt arbetsgivaravgift för unga
LIVSLANGD_MAN = (12, 24, 36, 48, 60, 72, 84, 96, 120)

def kr(x):  return f"{x:,.2f}".replace(",", " ")
def kr0(x): return f"{x:,.0f}".replace(",", " ")
def ref(v): return f"{v['serie']}{v['nr']}" if not str(v['serie'])[-1:].isdigit() else f"{v['serie']}:{v['nr']}"
def ar_lon(k): return "7000" <= k <= "7299" and not k.endswith("90")
def ar_fors(k): return k[:2] in ("30", "31")
def ar_utg_moms(k): return k[:3] in ("261", "262", "263")

def granska(bok, idag=None, handlingar=None):
    idag = idag or date.today()
    fynd = []
    def lagg(regel, v, beskr, forslag, allvar=None):
        r = KATALOG[regel]
        fynd.append({"regel": regel, "rubrik": r["regel"], "kalla": r["kalla"], "omrade": r["omrade"],
                     "allvar": allvar or int(r["allvar"]), "ver": ref(v) if v else "–",
                     "datum": str(v["datum"]) if v else "", "text": v["text"] if v else "",
                     "beskr": beskr, "forslag": forslag})

    rar_start, rar_slut = bok["rar"] or (None, None)
    avslutat = bool(rar_slut and rar_slut < idag)

    # Exakta motbokningar (verifikation + dess återföring) räknas bort ur bedömningsreglerna
    index = defaultdict(list)
    for v in bok["ver"]:
        index[tuple(sorted((k, round(b, 2)) for k, b in v["rader"]))].append(v)
    makulerade = set()
    for v in bok["ver"]:
        nyckel = tuple(sorted((k, round(-b, 2)) for k, b in v["rader"]))
        for w in index.get(nyckel, []):
            if w is not v and id(w) not in makulerade and id(v) not in makulerade:
                makulerade.update((id(v), id(w))); break
    aktiva = [v for v in bok["ver"] if id(v) not in makulerade]

    def sats_for(konto):
        m = re.search(r"(\d+)\s?%", bok["konton"].get(konto, ""))
        if m: return int(m.group(1)) / 100
        return {"261": 0.25, "262": 0.12, "263": 0.06}.get(konto[:3])

    def ar_korrigering(v):
        return "korrigering" in v["text"].lower() and len(v["rader"]) >= 6

    # ---- Grundbokföring ----
    for v in bok["ver"]:
        s = round(sum(b for _, b in v["rader"]), 2)
        if abs(s) > 0.005:
            lagg("BF01", v, f"Debet och kredit skiljer sig med {kr(s)} kr.", "Rätta verifikationen så att summan blir noll.")
    per_serie = defaultdict(list)
    for v in bok["ver"]:
        if isinstance(v["nr"], int): per_serie[v["serie"]].append(v["nr"])
    for serie, nr in per_serie.items():
        nr.sort()
        for a, b in zip(nr, nr[1:]):
            if a == b:
                lagg("BF03", None, f"Nummer {serie}{a} finns flera gånger.", "Varje verifikation ska ha ett eget nummer.")
            elif b - a > 1:
                lagg("BF02", None, f"Nummer {', '.join(f'{serie}{n}' for n in range(a + 1, b))} saknas.",
                     "Ta reda på om verifikationen raderats eller aldrig skapats, och dokumentera.")
    if rar_start:
        for v in bok["ver"]:
            if v["datum"] and not rar_start <= v["datum"] <= rar_slut:
                lagg("BF04", v, f"Räkenskapsåret är {rar_start}–{rar_slut}.", "Bokför på rätt år.")
    if bok["konton"]:
        for v in bok["ver"]:
            for k in sorted({k for k, _ in v["rader"] if k not in bok["konton"]}):
                lagg("BF05", v, f"Konto {k} saknas i kontoplanen.", "Troligen felskrivet kontonummer.")
    for v in bok["ver"]:
        if not v["text"].strip():
            lagg("BF06", v, "Det framgår inte vad affären gäller.", "Lägg till en kort text.")
        if v["andrade"]:
            lagg("BF07", v, f"{v['andrade']} rad(er) har lagts till eller tagits bort efter registreringen.",
                 "Kontrollera att ändringen är dokumenterad med datum och vem som gjorde den.")

    # Många verifikationer med samma registreringsdag = troligen en flytt från ett annat program, inte sen bokföring.
    per_dag = Counter(v["regdatum"] for v in bok["ver"] if v["regdatum"])
    forsta = min(per_dag) if per_dag else None   # flytten sker när programmet börjar användas
    flytt = {d for d, n in per_dag.items() if n >= 50 and n >= 0.2 * len(bok["ver"]) and (d - forsta).days <= 3}
    sena = sorted((v["regdatum"] - v["datum"]).days for v in bok["ver"]
                  if v["regdatum"] and v["datum"] and v["regdatum"] not in flytt and (v["regdatum"] - v["datum"]).days > 60)
    if sena:
        med = sena[len(sena) // 2]
        notis = "".join(f" {per_dag[d]} verifikationer registrerades samma dag ({d}), troligen vid byte av bokföringsprogram, och räknas inte." for d in sorted(flytt))
        lagg("BF10", None, f"{len(sena)} av {len(bok['ver'])} verifikationer bokfördes mer än 60 dagar efter affärshändelsen "
             f"(mitten {med} dagar, längst {sena[-1]} dagar).{notis}",
             "Kontrollera att bokföringen sker i tid. Företag med omsättning högst 3 mkr får vänta till betalning; kontanta betalningar ska alltid bokföras senast nästa arbetsdag.")

    def norm(t): return re.sub(r"\(.*?\)|[^a-zåäö0-9 ]", "", t.lower()).strip()   # siffror kvar: fakturanummer skiljer
    kostn = [(v, k, round(b, 2)) for v in aktiva if not any(k[0] == "3" for k, _ in v["rader"])
             for k, b in v["rader"] if k[0] in "456" and b >= 10]
    sedda = set()
    for i, (v1, k1, b1) in enumerate(kostn):
        for v2, k2, b2 in kostn[i + 1:]:
            if (k1 == k2 and b1 == b2 and v1 is not v2 and norm(v1["text"]) == norm(v2["text"])
                    and abs((v1["datum"] - v2["datum"]).days) <= 14 and (ref(v1), ref(v2)) not in sedda):
                sedda.add((ref(v1), ref(v2)))
                lagg("BF08", v2, f"Samma text, belopp ({kr(b1)} kr) och konto {k1} som {ref(v1)} den {v1['datum']}.",
                     "Kontrollera om samma faktura eller avgift bokförts två gånger.")

    # ---- Moms ----
    for v in aktiva:
        if ar_korrigering(v): continue
        konton = {k for k, _ in v["rader"]}
        moms = sum(b for k, b in v["rader"] if k in ("2640", "2641"))
        # personbil hanteras av MO10
        if "5615" in konton or "1240" in konton:
            leasing = sum(b for k, b in v["rader"] if k == "5615" and b > 0)
            if "1240" in konton and moms > 0:
                lagg("MO10", v, f"Ingående moms {kr(moms)} kr dras på köp av personbil.", "Momsen på personbil är inte avdragsgill; lägg den på bilens anskaffningsvärde.")
            elif leasing > 0 and moms > leasing * 0.125 + 1:
                lagg("MO10", v, f"Moms {kr(moms)} kr på leasing {kr(leasing)} kr motsvarar {moms / leasing * 100:.1f} %. Högst 12,5 % (halva momsen) får dras.",
                     "Dra av högst halva momsen; resten är kostnad.")
            continue
        if moms < 5: continue   # öresbelopp och avrundningar
        netto = sum(b for k, b in v["rader"] if k[0] in "4567" and b > 0 and k not in EJ_AVDRAG)
        if konton & EJ_AVDRAG and netto <= 0:
            lagg("MO03", v, f"Ingående moms {kr(moms)} kr dras på ej avdragsgill kostnad ({', '.join(sorted(konton & EJ_AVDRAG))}).",
                 "Ta bort momsavdraget och lägg hela beloppet som kostnad.")
            continue
        if netto > 0:
            kvot = moms / netto
            if any(abs(kvot - s) < 0.005 for s in MOMSSATSER): continue
            if 0.055 < kvot < 0.255:
                lagg("MO01", v, f"Moms {kr(moms)} kr på {kr(netto)} kr motsvarar {kvot * 100:.1f} %. Kan vara ett kvitto med blandade satser, eller ett fel.", "Stäm av mot kvittot.")
            else:
                lagg("MO02", v, f"Moms {kr(moms)} kr på {kr(netto)} kr motsvarar {kvot * 100:.1f} %, utanför alla svenska momssatser.", "Rätta momsbeloppet mot kvittot.")

    def momsfri(k):   # enligt BAS-listan eller kontots eget namn i filen
        return k in MOMSFRIA_FORS or bool(re.search(r"momsfri|ej moms|utan moms", bok["konton"].get(k, ""), re.I))
    def momspl(k):    # försäljning som ska ha moms: 30–31, eller annat 3-konto vars namn säger moms
        if k[0] != "3" or momsfri(k): return False
        return ar_fors(k) or bool(re.search(r"momspl|moms\s*\d+\s*%", bok["konton"].get(k, ""), re.I))
    def omforing(v):   # bara resultatkonton: flytt mellan konton, ingen affär
        return all(k[0] in "345678" for k, _ in v["rader"])
    for v in aktiva:
        if ar_korrigering(v) or omforing(v): continue
        if any(k[:2] in ("17", "29") for k, _ in v["rader"]): continue   # periodisering: momsen redovisades vid faktureringen
        forsalj = -sum(b for k, b in v["rader"] if momspl(k))
        utgrader = [(k, -b) for k, b in v["rader"] if ar_utg_moms(k) and k[3] in "01237"]
        if forsalj > 0:
            if not utgrader:
                if not any(momsfri(k) for k, _ in v["rader"]):
                    lagg("MO05", v, f"Försäljning {kr(forsalj)} kr bokförd utan moms.", "Kontrollera om försäljningen är momsfri; annars lägg till utgående moms.")
            elif all(sats_for(k) for k, _ in utgrader):
                underlag = sum(m / sats_for(k) for k, m in utgrader)
                if abs(underlag - forsalj) > max(1.0, forsalj * 0.01):
                    utg = sum(m for _, m in utgrader)
                    fel = abs(underlag - forsalj) * utg / underlag
                    lagg("MO04", v, f"Försäljning {kr(forsalj)} kr, men momsen {kr(utg)} kr motsvarar ett underlag på {kr(underlag)} kr. Momsen avviker med cirka {kr(fel)} kr.",
                         "Rätta momsbeloppet eller försäljningskontot.", allvar=1 if fel >= 50 else 2)
        minsk = sum(b for k, b in v["rader"] if momspl(k) and b > 0)
        okn = sum(-b for k, b in v["rader"] if momspl(k) and b < 0)
        if minsk > 0 and okn == 0 and not any(ar_utg_moms(k) for k, _ in v["rader"]) \
                and not any(momsfri(k) or k[:2] in ("17", "29") for k, _ in v["rader"]):
            lagg("MO06", v, f"{kr(minsk)} kr bokas som minskad försäljning, men utgående moms rättas inte.",
                 "Om det är en kreditering ska även momsen krediteras. Om det är en kostnad ska den bokas på ett kostnadskonto.")

    for v in aktiva:
        omv = -sum(b for k, b in v["rader"] if k in ("2614", "2624", "2634"))
        ber = sum(b for k, b in v["rader"] if k in ("2645", "2647"))
        if (omv or ber) and abs(omv - ber) > 1:
            lagg("MO09", v, f"Utgående moms omvänd skattskyldighet {kr(omv)} kr men beräknad ingående moms {kr(ber)} kr.",
                 "Beloppen ska vara lika stora i samma verifikation.")

    if bok["har_ib"]:
        kvar = {k: b for k, b in bok["ib"].items() if k[:3] in ("261", "262", "263", "264") and abs(b) > 0.5}
        omfort = {k for v in bok["ver"] for k, b in v["rader"] if k in kvar and abs(b + kvar[k]) < 0.01}
        kvar = {k: b for k, b in kvar.items() if k not in omfort}
        if kvar:
            netto = sum(kvar.values())
            lagg("MO07", None, f"Momskontona har ingående saldon som inte förts över till 2650: {', '.join(f'{k} {kr(b)}' for k, b in sorted(kvar.items()))}. Netto {kr(abs(netto))} kr att {'få tillbaka' if netto > 0 else 'betala'}.",
                 "Kontrollera att momsdeklarationen är inlämnad och bokför momsredovisningen mot 2650.")
    if bok["ub"] and avslutat:
        kvar = {k: b for k, b in bok["ub"].items() if k[:3] in ("261", "262", "263", "264") and abs(b) > 0.5}
        if kvar:
            netto = sum(kvar.values())
            lagg("MO08", None, f"Vid årets slut står momskontona kvar med saldon: {', '.join(f'{k} {kr(b)}' for k, b in sorted(kvar.items()))}. Netto {kr(abs(netto))} kr att {'få tillbaka' if netto > 0 else 'betala'}.",
                 "Kontrollera att momsdeklarationen är inlämnad och bokför momsredovisningen mot 2650.")

    # ---- Skatt ----
    for v in aktiva:
        t = v["text"].lower()
        traff = [o for o in PRIVATA_ORD if re.search(r"(?<![a-zåäö])" + re.escape(o) + r"(?![a-zåäö])", t)]
        if not traff or not any(k[0] in "4567" for k, _ in v["rader"]): continue
        if any(k in EJ_AVDRAG for k, _ in v["rader"]) and not any(k.startswith("264") for k, _ in v["rader"]): continue
        lagg("SK01", v, f"Texten innehåller ”{traff[0]}”, vilket ofta är en privat kostnad.",
             "Kontrollera syftet. Privata utgifter bokas mot eget uttag eller som lön/förmån.")

    # ---- Lön ----
    lonesumma = 0.0
    for v in aktiva:
        lon = sum(b for k, b in v["rader"] if ar_lon(k) and b > 0)
        if lon <= 0: continue
        lonesumma += lon
        if not any(k == "2710" for k, _ in v["rader"]):
            lagg("LO01", v, f"Lön {kr(lon)} kr bokförd utan personalskatt (2710).", "Kontrollera att skatteavdrag gjorts och redovisats.")
        avg = sum(b for k, b in v["rader"] if k in ("7510", "7511", "7512"))
        unga = v["datum"] and UNGA_AVGIFT[0] <= v["datum"] <= UNGA_AVGIFT[1] and UNGA_AVGIFT[2] - 0.002 <= avg / lon <= 0.3142 + 0.002
        if avg and not unga and not any(abs(avg / lon - s) < 0.002 for s in (0.3142, 0.1021)):
            lagg("LO02", v, f"Arbetsgivaravgift {kr(avg)} kr på lön {kr(lon)} kr motsvarar {avg / lon * 100:.2f} %.",
                 "Kontrollera mot arbetsgivardeklarationen och om nedsatt avgift gäller.")
    if avslutat and lonesumma > 0:
        s2920 = bok["ib"].get("2920", 0) + sum(b for v in bok["ver"] for k, b in v["rader"] if k == "2920")
        if abs(s2920) < 0.5:
            lagg("LO03", None, f"Löner på {kr0(lonesumma)} kr under året men ingen semesterlöneskuld på 2920 vid årets slut.",
                 "Beräkna och boka semesterlöneskulden vid bokslutet.")

    # ---- Avskrivningar ----
    def ar_tillgang(k): return k.startswith("12") and k[3] != "9" and k[2] in "12345"
    anskaffad = sum(b for k, b in bok["ib"].items() if ar_tillgang(k))
    if rar_slut:
        anskaffad += sum(b for v in bok["ver"] for k, b in v["rader"]
                         if ar_tillgang(k) and b > 0 and v["datum"] and (rar_slut - v["datum"]).days >= 90)
    avskr_rader = [(v, k, b) for v in bok["ver"] for k, b in v["rader"] if k.startswith("78") and b > 0]
    if anskaffad > 0 and not avskr_rader and rar_start:
        slut = min(idag, rar_slut)
        man = (slut.year - rar_start.year) * 12 + slut.month - rar_start.month + (1 if slut == rar_slut else 0)  # hela månader
        if avslutat:
            lagg("AV01", None, f"Inventarier för {kr0(anskaffad)} kr men inga avskrivningar under räkenskapsåret.",
                 "Boka årets avskrivningar.")
        elif man >= 6:
            lagg("AV01", None, f"Inventarier för {kr0(anskaffad)} kr men inga avskrivningar bokförda de första {man} månaderna.",
                 "Om ni skriver av månadsvis saknas avskrivningar; annars bokas de i bokslutet.", allvar=2)
    belopp = sorted({round(b, 2) for _, _, b in avskr_rader})
    for v in bok["ver"]:
        tillg = sum(b for k, b in v["rader"] if ar_tillgang(k) and b > 0)
        moms = sum(b for k, b in v["rader"] if k in ("2640", "2641") and b > 0)
        if tillg <= 0 or moms <= 0: continue
        brutto = tillg + moms
        for m in belopp:
            traff = [n for n in LIVSLANGD_MAN if abs(m * n - brutto) <= brutto * 0.015 and abs(m * n - tillg) > tillg * 0.03]
            if traff:
                lagg("AV02", v, f"Avskrivning {kr(m)} kr/månad × {traff[0]} månader = {kr(m * traff[0])} kr, vilket motsvarar priset inklusive moms ({kr(brutto)} kr). Momsen ({kr(moms)} kr) är redan avdragen, så avskrivningen ska räknas på {kr(tillg)} kr.",
                     f"Rätta avskrivningen till cirka {kr(tillg / traff[0])} kr/månad.")
                break
    for v in bok["ver"]:
        grans = PBB.get(v["datum"].year, max(PBB.values())) / 2 if v["datum"] else None
        for k, b in v["rader"]:
            if "5400" <= k <= "5419" and grans and b >= grans:
                lagg("AV03", v, f"{kr(b)} kr kostnadsförs direkt på {k}, över halvt prisbasbelopp ({kr0(grans)} kr).",
                     "Kontrollera om det är en inventarie som ska tas upp som tillgång och skrivas av.")

    # ---- Bank och kassa ----
    konton19 = sorted({k for v in bok["ver"] for k, _ in v["rader"] if k.startswith("19")} | {k for k in bok["ib"] if k.startswith("19")})
    for konto in konton19:
        # Saldot räknas vid dagens slut: inom en dag spelar bokföringsordningen ingen roll.
        per_dag = defaultdict(float); sista = {}
        for v in bok["ver"]:
            if not v["datum"]: continue
            for k, b in v["rader"]:
                if k == konto: per_dag[v["datum"]] += b; sista[v["datum"]] = v
        saldo = bok["ib"].get(konto, 0.0); neg = []
        for d in sorted(per_dag):
            saldo += per_dag[d]
            if saldo < -0.005: neg.append((d, saldo))
        if neg:
            namn = "kassan" if konto == "1910" else f"konto {konto} ({bok['konton'].get(konto, '')})"
            d0, s0 = neg[0]; lagst = min(neg, key=lambda x: x[1])
            mer = f" Det händer {len(neg)} dagar under perioden, som lägst {kr(lagst[1])} kr den {lagst[0]}." if len(neg) > 1 else ""
            lagg("BA01", sista[d0], f"Saldot på {namn} är {kr(s0)} kr vid dagens slut den {d0}.{mer}",
                 "Stäm av mot kontoutdraget. Stämmer det är kontot övertrasserat; annars saknas en insättning eller ett ingående saldo, eller fel konto används.")
    anvanda = {k for v in bok["ver"] for k, _ in v["rader"] if k.startswith("19")}
    for konto, ib in bok["ib"].items():
        if konto.startswith("19") and konto != "1910" and abs(ib) > 0.005 and konto not in anvanda and anvanda:
            lagg("BA02", None, f"Konto {konto} har ingående saldo {kr(ib)} kr men inga transaktioner, medan banken bokförs på {', '.join(sorted(anvanda))}.",
                 "Kontrollera om banken bytt konto i bokföringen; flytta i så fall saldot.")

    # ---- Aktiebolag ----
    saldon = defaultdict(float, bok["ib"])
    for v in bok["ver"]:
        for k, b in v["rader"]: saldon[k] += b
    aktiekapital = -saldon.get("2081", 0.0)
    if aktiekapital > 0:
        ek = -sum(b for k, b in saldon.items() if k.startswith("20")) - sum(b for k, b in saldon.items() if k[0] in "345678")
        if ek < aktiekapital / 2:
            lagg("AB01", None, f"Eget kapital är {kr0(ek)} kr mot aktiekapital {kr0(aktiekapital)} kr.",
                 "Ta upp med styrelsen direkt; kontrollbalansräkning kan krävas och personligt ansvar kan uppstå.")
    for k, s in (saldon.items() if aktiekapital > 0 else []):   # aktiebolagsreglerna gäller bara aktiebolag
        namn = bok["konton"].get(k, "").lower()
        if "1680" <= k <= "1689" and (k == "1685" or re.search(r"delägare|aktieägare|närstående|ägare", namn)) and s > 0.5:
            lagg("AB02", None, f"Konto {k} ({bok['konton'].get(k, '')}) har ett saldo på {kr(s)} kr.",
                 "Lån till aktieägare och närstående är i regel förbjudna; kontrollera vad fordran avser.")
    if aktiekapital > 0 and bok["har_ib"] and abs(bok["ib"].get("2099", 0)) > 0.5 and not any(k == "2099" for v in bok["ver"] for k, _ in v["rader"]
                                                           if not any(x == "8999" for x, _ in v["rader"])):   # bokningen av årets resultat räknas inte
        lagg("AB03", None, f"Fjolårets resultat ({kr(-bok['ib']['2099'])} kr) ligger kvar på 2099 Årets resultat.",
             "Omför till 2098/2091 enligt årsstämmans beslut.")


    # ---- Bokslut, skatt och fastighet (tillagt 2026-10-06 efter genomgång mot lag, BFN och Skatteverket) ----
    def saldo_ub(fran, till):
        return sum(b for k, b in saldon.items() if fran <= k <= till)
    def namn(k): return bok["konton"].get(k, "")
    resultat_fore = -sum(b for v in bok["ver"] for k, b in v["rader"] if "3000" <= k <= "8799")
    har_8999 = any(k == "8999" for v in bok["ver"] for k, _ in v["rader"])
    arsres = -sum(b for v in bok["ver"] for k, b in v["rader"] if "3000" <= k <= "8989")
    oms = -sum(b for v in bok["ver"] for k, b in v["rader"] if "3000" <= k <= "3799")
    balans = sum(b for k, b in saldon.items() if k[0] == "1" and b > 0)
    ar = rar_slut.year if rar_slut else idag.year

    # BF12 kontanta betalningar
    sena_kassa = [v for v in aktiva if v["regdatum"] and v["datum"] and any(k == "1910" for k, _ in v["rader"])
                  and (v["regdatum"] - v["datum"]).days > 3]
    if sena_kassa:
        lagg("BF12", sena_kassa[0], f"{len(sena_kassa)} kassaposter registrerades mer än tre dagar efter betalningen.",
             "Kontanta in- och utbetalningar ska bokföras senast nästa arbetsdag.")

    # MO13 blandad verksamhet
    fri = -sum(b for v in aktiva for k, b in v["rader"] if k[0] == "3" and momsfri(k))
    pliktig = -sum(b for v in aktiva for k, b in v["rader"] if momspl(k))
    ingmoms = sum(b for v in aktiva for k, b in v["rader"] if k in ("2640", "2641", "2645", "2647") and b > 0)
    if fri > 1000 and pliktig > 1000 and ingmoms > 0:
        andel = pliktig / (pliktig + fri)
        lagg("MO13", None, f"Momsfri försäljning {kr0(fri)} kr och momspliktig {kr0(pliktig)} kr under året, och ingående moms {kr0(ingmoms)} kr har dragits av. Momspliktig andel {andel * 100:.0f} %.",
             "Moms på kostnader som hör till den momsfria delen (t.ex. bostadsuthyrning) får inte dras av. Gemensamma kostnader fördelas efter skälig grund, ofta omsättningen.")

    # SK06 ränteavdragsbegränsning
    rantenetto = sum(b for v in aktiva for k, b in v["rader"] if "8400" <= k <= "8499" and k != "8423") \
                 + sum(b for v in aktiva for k, b in v["rader"] if "8300" <= k <= "8399")
    if rantenetto > 5_000_000:
        lagg("SK06", None, f"Negativt räntenetto {kr0(rantenetto)} kr, över förenklingsregelns 5 000 000 kr.",
             "Avdraget begränsas till 30 % av skattemässigt EBITDA. Gränsen 5 mkr gäller för hela intressegemenskapen.")
    elif rantenetto > 1_000_000:
        lagg("SK06", None, f"Negativt räntenetto {kr0(rantenetto)} kr i bolaget.",
             "Förenklingsregelns 5 mkr delas av alla bolag i intressegemenskapen (koncernen). Lägg ihop räntenettot för hela gruppen innan deklarationen.", allvar=3)

    # SK07 ej avdragsgilla kostnader
    ejavdr = defaultdict(float)
    for v in aktiva:
        for k, b in v["rader"]:
            if k[0] in "5678" and (k in ("6072", "6982", "6992", "7622", "7632", "8423")
                                   or re.search(r"ej avdr|icke avdr|skattetillägg|förseningsavgift|böter|kontrollavgift", namn(k), re.I)):
                ejavdr[k] += b
    ejavdr = {k: b for k, b in ejavdr.items() if b > 0.5}
    if ejavdr:
        lagg("SK07", None, "Ej avdragsgilla kostnader: " + "; ".join(f"{k} {namn(k)} {kr0(b)} kr" for k, b in sorted(ejavdr.items()))
             + f". Sammanlagt {kr0(sum(ejavdr.values()))} kr.", "Lägg tillbaka beloppet i inkomstdeklarationen.")

    # SK08 periodiseringsfonder
    fonder = []
    for k in sorted({k for k in saldon if "2110" <= k <= "2149"}):
        m = re.search(r"(20\d\d)", namn(k))
        if m and abs(saldon[k]) > 0.5: fonder.append((k, int(m.group(1)), -saldon[k], -bok["ib"].get(k, 0.0)))
    for k, y, s, ib in fonder:
        if ar >= y + 6:
            sist = ar == y + 6
            lagg("SK08", None, f"Periodiseringsfond {y} (konto {k}) på {kr0(s)} kr står kvar. Den ska återföras senast beskattningsåret {y + 6}.",
                 "Återför fonden till beskattning (konto 8819/2110-gruppen).", allvar=1 if (ar > y + 6 or (sist and avslutat)) else 2)
    ib_fonder = sum(ib for _, _, _, ib in fonder if ib > 0)
    if ib_fonder > 0 and ar in STATSLANERANTA:
        lagg("SK08", None, f"Periodiseringsfonder vid årets början {kr0(ib_fonder)} kr ger en schablonintäkt på {kr0(ib_fonder * STATSLANERANTA[ar])} kr ({STATSLANERANTA[ar] * 100:.2f} %).",
             "Ta upp schablonintäkten i inkomstdeklarationen.", allvar=3)

    # SK09 bolagsskatt saknas
    if aktiekapital > 0 and avslutat and har_8999 and resultat_fore > 1000 and not any("8900" <= k <= "8989" for v in bok["ver"] for k, _ in v["rader"]):
        lagg("SK09", None, f"Resultatet före skatt är {kr0(resultat_fore)} kr men ingen skatt är bokförd.",
             "Beräkna och boka årets skatt (20,6 %), om inte underskott från tidigare år täcker vinsten.")

    # FA01 fastighetsskatt / AV04 byggnader / AV05 mark
    fastighet = saldo_ub("1110", "1159")
    if avslutat and fastighet > 0 and not any(k == "5191" or re.search(r"fastighetsskatt|fastighetsavgift", namn(k) + " " + v["text"], re.I)
                                             for v in aktiva for k, b in v["rader"] if k[0] in "5678"):
        lagg("FA01", None, f"Byggnader och mark för {kr0(fastighet)} kr i balansräkningen, men ingen fastighetsskatt eller fastighetsavgift bokförd.",
             "Kontrollera om fastigheten är taxerad och om skatt eller avgift ska betalas (nybyggda bostäder kan vara befriade).")
    byggnader = saldo_ub("1110", "1118")
    if avslutat and byggnader > 0 and not any(("1110" <= k <= "1119" and b < 0) or "7820" <= k <= "7829" for v in aktiva for k, b in v["rader"]):
        lagg("AV04", None, f"Byggnader för {kr0(byggnader)} kr men ingen avskrivning under året.", "Boka årets avskrivning på byggnaderna (mark skrivs inte av).")
    for v in aktiva:
        if any("1130" <= k <= "1139" and b < 0 for k, b in v["rader"]) and any(k.startswith("78") and b > 0 for k, b in v["rader"]):
            lagg("AV05", v, "Avskrivning bokförd mot markkonto.", "Mark får inte skrivas av; rätta verifikationen.")

    # BO06 bokslut ej bokfört
    if avslutat and (idag - rar_slut).days > 182 and not har_8999 and abs(arsres) > 0.5:
        lagg("BO06", None, f"Räkenskapsåret slutade {rar_slut} men årets resultat ({kr0(arsres)} kr) är inte bokfört mot eget kapital.",
             "Gör och boka bokslutet. Ett aktiebolags årsredovisning ska vara hos Bolagsverket inom sju månader, annars tas förseningsavgift ut.")

    # BO07 kontantmetod med för hög omsättning
    if oms > 3_000_000 and not any(("1510" <= k <= "1519" or "2440" <= k <= "2449") for v in aktiva for k, _ in v["rader"]):
        lagg("BO07", None, f"Nettoomsättningen är {kr0(oms)} kr men inga kundfordringar eller leverantörsskulder är bokförda.",
             "Över 3 mkr i omsättning ska fakturor bokföras när de kommer in och skickas ut (faktureringsmetoden).")

    # BO08 orimligt tecken / BO09 oklara poster
    if avslutat:
        for k, s in sorted(saldon.items()):
            if ("1510" <= k <= "1519" and s < -1) or (("2440" <= k <= "2449" or k == "2710") and s > 1):
                lagg("BO08", None, f"Konto {k} ({namn(k)}) har saldo {kr(s)} kr vid årets slut, med fel tecken för kontotypen.",
                     "Utred posten – ofta en dubbel betalning, en felaktigt bokad faktura eller en kreditnota som inte kvittats.")
            if k[0] in "12" and abs(s) > 1 and re.search(r"\bobs\b|oklar|outred|utredning|felbok|okänd", namn(k), re.I):
                lagg("BO09", None, f"Konto {k} ({namn(k)}) har saldo {kr(s)} kr vid årets slut.", "Utred och boka om posterna till rätt konto före bokslutet.")

    # AB05 revisor / AB06 större företag / AB07 utdelning
    if aktiekapital > 0 and balans > 1_500_000 and oms > 3_000_000:
        lagg("AB05", None, f"Balansomslutning {kr0(balans)} kr och nettoomsättning {kr0(oms)} kr – båda över gränserna (1,5 mkr och 3 mkr).",
             "Gällde det även förra året krävs revisor, även om bolagsordningen säger annat.")
    elif aktiekapital > 0 and (balans > 1_500_000 or oms > 3_000_000) and lonesumma > 0:
        over = f"balansomslutning {kr0(balans)} kr" if balans > 1_500_000 else f"nettoomsättning {kr0(oms)} kr"
        lagg("AB05", None, f"Bolaget har {over}, över gränsen, och har anställda.",
             "Har bolaget haft fler än tre anställda i medeltal både i år och förra året krävs revisor.", allvar=3)
    if aktiekapital > 0 and balans > 40_000_000 and oms > 80_000_000:
        lagg("AB06", None, f"Balansomslutning {kr0(balans)} kr och nettoomsättning {kr0(oms)} kr.",
             "Två år i rad över gränserna gör bolaget till ett större företag: K2 får inte användas och fler krav gäller.")
    utd = sum(-b for v in aktiva for k, b in v["rader"] if k == "2898" and b < 0)
    fritt = -sum(b for k, b in bok["ib"].items() if "2090" <= k <= "2099")
    if aktiekapital > 0 and bok["har_ib"] and utd > 0.5 and utd > fritt + 0.5:
        lagg("AB07", None, f"Utdelning {kr0(utd)} kr men fritt eget kapital vid årets början var {kr0(fritt)} kr.",
             "Utdelning får inte överstiga fritt eget kapital; olaglig utdelning ska betalas tillbaka.")

    # ---- Lager 2: avstämning mot handlingar som användaren fyllt i ----
    bok["_avstamning"] = []
    if handlingar:
        import avstamning
        bok["_avstamning"] = avstamning.avstam(bok, handlingar, lagg)
    fynd.sort(key=lambda f: (f["allvar"], f["regel"], int(re.sub(r"\D", "", f["ver"]) or 0)))
    return fynd

# ---------- Rapport ----------
LOGGA = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 60" width="200" role="img" aria-label="Nordwik Partners">
<g transform="translate(6,10)" fill="none" stroke="#141A16" stroke-width="2"><rect x="0" y="0" width="40" height="40"/>
<line x1="0" y1="15" x2="40" y2="15"/><line x1="22" y1="0" x2="22" y2="15"/><line x1="22" y1="15" x2="22" y2="40"/>
<rect x="22" y="15" width="18" height="25" fill="#4E7A45" stroke="none"/></g>
<text x="62" y="30" font-family="Newsreader, Georgia, serif" font-size="26" font-weight="600" letter-spacing="1" fill="#141A16">NORDWIK</text>
<text x="63" y="47" font-family="'IBM Plex Mono', monospace" font-size="11" font-weight="500" letter-spacing="4.5" fill="#4E7A45">PARTNERS</text></svg>'''
STIL = """:root{--text:#141A16;--gron:#4E7A45;--mork:#1E3A31;--papper:#F4F3EF;--sek:#4A524D;--dim:#6B726E;--linje:#C4C9C5;--vit:#FFFFFF}
body{margin:0;background:var(--papper);color:var(--text);font-family:Inter,system-ui,sans-serif;font-size:15px;line-height:1.5}
.wrap{max-width:1040px;margin:0 auto;padding:32px 16px}h1{font-weight:800;letter-spacing:-.03em;font-size:30px;margin:24px 0 4px}
h2{font-weight:800;font-size:20px;margin:32px 0 8px}.sub{color:var(--sek)}.kort{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}
.k{background:var(--vit);border:1px solid var(--linje);padding:14px 18px;min-width:150px}.k b{display:block;font-size:28px;font-weight:800;font-family:'IBM Plex Mono',monospace}
table{width:100%;border-collapse:collapse;background:var(--vit);border:1px solid var(--linje)}th{text-align:left;background:var(--mork);color:var(--vit);font-weight:600;padding:10px}
td{padding:10px;border-top:1px solid var(--linje);vertical-align:top}.tag{color:#fff;font-size:12px;font-weight:600;padding:2px 8px;white-space:nowrap}
.mono{font-family:'IBM Plex Mono',monospace}.dim{color:var(--dim);font-size:13px}.ruta{background:var(--vit);border-left:4px solid var(--gron);padding:12px 16px;margin:16px 0}
.fot{margin-top:28px;color:var(--dim);font-size:13px;border-top:1px solid var(--linje);padding-top:12px}
@media(max-width:700px){table,tr,td,th{display:block}th{display:none}td{border:0}tr{border-top:1px solid var(--linje);padding:8px 0}}"""
HUVUD = ('<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>TITEL</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=IBM+Plex+Mono:wght@500&family=Newsreader:wght@600&display=swap" rel="stylesheet">'
         '<style>' + STIL + '</style></head><body><div class="wrap">' + LOGGA)
FOT = ('<div class="fot">Kansliet at Nordwik Partners · kansliet@nordwikpartners.se</div></div></body></html>')
ALLVAR = {1: ("Allvarligt", "#9B2C1F"), 2: ("Bör kontrolleras", "#9A6A12"), 3: ("Notering", "#6B726E")}

def rapport(bok, fynd, idag=None):
    e = html.escape
    idag = idag or date.today()
    antal = {n: sum(1 for f in fynd if f["allvar"] == n) for n in (1, 2, 3)}
    aktiva = sum(1 for r in KATALOG.values() if r["status"] == "aktiv")
    rar = f"{bok['rar'][0]} – {bok['rar'][1]}" if bok["rar"] else "okänt"
    rader = "".join(
        f'<tr><td><span class="tag" style="background:{ALLVAR[f["allvar"]][1]}">{ALLVAR[f["allvar"]][0]}</span></td>'
        f'<td class="mono">{e(f["ver"])}<br><span class="dim">{e(f["datum"])}</span></td>'
        f'<td><strong>{e(f["rubrik"])}</strong> <span class="dim mono">{f["regel"]}</span><br>{e(f["beskr"])}'
        f'{"<br><span class=dim>Verifikationstext: " + e(f["text"]) + "</span>" if f["text"] else ""}'
        f'<br><span class="dim">Regel: {e(f["kalla"])}</span></td><td>{e(f["forslag"])}</td></tr>' for f in fynd) \
        or '<tr><td colspan="4">Inga avvikelser hittades.</td></tr>'
    return (HUVUD.replace("TITEL", "Granskningsrapport") +
            f'<h1>Granskningsrapport</h1><div class="sub">{e(bok["namn"])} · {e(bok["orgnr"])} · Räkenskapsår {rar} · Granskad {idag}</div>'
            f'<div class="ruta"><strong>Vad som inte har kontrollerats.</strong> Granskningen bygger enbart på bokföringsfilen (SIE). '
            f'Kvitton, fakturor och avtal har inte setts. Deklarationer, skattekonto och bankens saldon har inte jämförts om de inte bifogats. '
            f'Rapporten är inte en revision och intygar inte att bokföringen i övrigt är korrekt. {aktiva} regler har körts.</div>'
            f'<div class="kort"><div class="k"><b>{len(bok["ver"])}</b>verifikationer</div>'
            f'<div class="k"><b style="color:#9B2C1F">{antal[1]}</b>allvarliga</div><div class="k"><b style="color:#9A6A12">{antal[2]}</b>bör kontrolleras</div>'
            f'<div class="k"><b style="color:#6B726E">{antal[3]}</b>noteringar</div></div>'
            f'<table><tr><th>Allvar</th><th>Verifikation</th><th>Vad vi hittade</th><th>Förslag</th></tr>{rader}</table>' + FOT)

if __name__ == "__main__":
    idag = date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else None
    bok = las_sie(sys.argv[1])
    fynd = granska(bok, idag)
    if len(sys.argv) > 2:
        open(sys.argv[2], "w", encoding="utf-8").write(rapport(bok, fynd, idag))
    for f in fynd:
        print(f["allvar"], f["regel"], f["ver"], "|", f["beskr"])
    print(f"{len(fynd)} fynd")
