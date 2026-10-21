"""Tester för "Så mycket hade Konrad bokfört själv" (py/konrad_andel.py). Körs från repots rot:

    python3 -m unittest discover -s tester -p 'aiauditor_test_*.py'

Facit är räknat för hand (och kontrollräknat av en separat genomgång 2026-10-21) på exempel-sie.txt
och två påhittade filer i tester/data/. Testerna garanterar också att byråversionen aldrig nämner Konrad."""
import json, shutil, subprocess, sys, tempfile, unittest
from datetime import date
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROT / "py"))
import granskaren as g  # noqa: E402
import konrad_andel as ka  # noqa: E402
import nyckeltal as n  # noqa: E402
import rapport as r  # noqa: E402

DATA = ROT / "tester" / "data"
IDAG = date(2026, 10, 12)
FIL1_FYND = [{"ver": "A6"}]
FIL2_FYND = [{"ver": "1:3"}, {"ver": "–"}]


def facit(res):
    return {x["ver"]: (x["auto"], x["skal"]) for x in res["verifikationer"]}


class Exempelfilen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bok = g.las_sie(str(ROT / "exempel-sie.txt"))
        cls.fynd = g.granska(cls.bok, IDAG)
        cls.res = ka.berakna(cls.bok, cls.fynd)

    def test_antal(self):
        self.assertEqual((self.res["totalt"], self.res["auto"], self.res["manniska"]), (95, 58, 37))
        self.assertAlmostEqual(self.res["andel_auto"], 58 / 95)

    def test_vilka_till_manniska(self):
        manniska = [x["ver"] for x in self.res["verifikationer"] if not x["auto"]]
        lon_och_fakturor = {f"A{i}" for i in (3, 4, 9, 10, 16, 17, 23, 24, 30, 31, 39, 41, 47, 48, 54, 56, 63, 64,
                                               71, 72, 81, 82, 83, 89, 90, 91)}
        ovriga = {"A14", "A20", "A35", "A36", "A40", "A55", "A60", "A69", "A77", "A94", "A95"}
        self.assertEqual(set(manniska), lon_och_fakturor | ovriga)

    def test_skal(self):
        self.assertEqual([(s["id"], s["antal"]) for s in self.res["skal"]],
                         [("STORT", 28), ("SALLAN", 8), ("FYND", 4), ("REPR", 2), ("BOKSLUT", 2), ("SARMOMS", 2),
                          ("INVEST", 1), ("RATTELSE", 1)])
        f = facit(self.res)
        self.assertEqual(f["A14"], (False, ["STORT", "INVEST", "SALLAN"]))
        self.assertEqual(f["A20"], (False, ["FYND", "REPR", "SALLAN"]))
        self.assertEqual(f["A55"], (False, ["SARMOMS", "SALLAN"]))
        self.assertEqual(f["A77"], (False, ["RATTELSE"]))
        self.assertEqual(f["A94"], (False, ["BOKSLUT", "SALLAN"]))
        self.assertEqual(f["A95"], (False, ["STORT", "BOKSLUT", "SARMOMS"]))
        self.assertEqual(f["A76"], (True, []))
        self.assertEqual(f["A5"], (True, []))  # avskrivning: återkommande utan bank

    def test_tid(self):
        t = ka.tid(58)
        self.assertAlmostEqual(t["timmar"], 58 * 5 / 60)
        self.assertIsNone(t["kronor"])
        self.assertEqual(ka.tid(58, 5, 600)["kronor"], 2900)
        self.assertEqual(ka.tid(58, 7.5, 450)["kronor"], 3263)  # 7,25 h × 450 = 3 262,5 → avrundas uppåt som i JS
        self.assertEqual(ka.tid(0, 5, 600)["timmar"], 0)


class PahittadeFiler(unittest.TestCase):
    def test_fil1(self):
        res = ka.berakna(g.las_sie(str(DATA / "konrad-fil1.se")), FIL1_FYND)
        self.assertEqual((res["totalt"], res["auto"], res["manniska"]), (18, 9, 9))  # A16 är tom och räknas inte
        self.assertEqual(facit(res), {
            "A1": (True, []), "A2": (True, []), "A3": (True, []),
            "A4": (False, ["MONSTER"]), "A5": (False, ["MONSTER"]), "A6": (False, ["FYND"]),
            "A7": (True, []), "A8": (True, []), "A9": (True, []),
            "A10": (False, ["MOMS", "SALLAN"]), "A11": (False, ["MOMS", "SALLAN"]),
            "A12": (False, ["AGARE", "SALLAN"]), "A13": (False, ["INVEST", "SALLAN"]),
            "A14": (False, ["STORT", "INVEST", "SALLAN"]), "A15": (False, ["RATTELSE"]),
            "B1": (True, []), "B2": (True, []), "B3": (True, [])})  # månadsnamn räknas bort: återkommande
        self.assertEqual([(s["id"], s["antal"]) for s in res["skal"]],
                         [("SALLAN", 5), ("MOMS", 2), ("INVEST", 2), ("MONSTER", 2), ("STORT", 1), ("FYND", 1),
                          ("AGARE", 1), ("RATTELSE", 1)])

    def test_fil2(self):
        res = ka.berakna(g.las_sie(str(DATA / "konrad-fil2.se")), FIL2_FYND)
        self.assertEqual((res["totalt"], res["auto"], res["manniska"]), (17, 8, 9))
        self.assertEqual(facit(res), {
            "1:1": (True, []), "1:2": (True, []), "1:3": (False, ["FYND"]),
            "1:4": (False, ["SALLAN"]), "1:5": (False, ["REPR", "SALLAN"]), "1:6": (False, ["STORT"]),
            "1:7": (True, []), "1:8": (False, ["MOMS"]), "1:9": (False, ["STORT"]),
            "1:10": (True, []), "1:11": (True, []), "1:12": (False, ["BOKSLUT", "SALLAN"]),
            "1:13": (False, ["SARMOMS", "SALLAN"]), "1:14": (True, []), "1:15": (True, []), "1:16": (True, []),
            "1:17": (False, ["RATTELSE"])})

    def test_gransen_ar_over_25000(self):
        f = facit(ka.berakna(g.las_sie(str(DATA / "konrad-fil1.se")), FIL1_FYND))
        self.assertNotIn("STORT", f["A13"][1])  # exakt 25 000 kr
        self.assertIn("STORT", f["A14"][1])     # 25 000,01 kr


class BaraGratisversionen(unittest.TestCase):
    """Olles beslut 20 okt 2026: gratisversionen visar Konrad, byråversionen ALDRIG."""
    FILER = [ROT / "exempel-sie.txt", DATA / "konrad-fil1.se", DATA / "konrad-fil2.se"]

    def bygg(self, sokvag, variant, webb):
        bok = g.las_sie(str(sokvag))
        ut = r.bygg(bok, g.granska(bok, IDAG), IDAG, None, webb=webb, variant=variant)
        return "".join(ut) if webb else ut

    def test_byraversionen_namner_aldrig_konrad(self):
        for sokvag in self.FILER:
            for variant in ("byra", None):
                for webb in (True, False):
                    with self.subTest(fil=sokvag.name, variant=variant, webb=webb):
                        self.assertNotIn("konrad", self.bygg(sokvag, variant, webb).lower())

    def test_gratisversionen_visar_avsnittet(self):
        for sokvag in self.FILER:
            for webb in (True, False):
                ut = self.bygg(sokvag, "gratis", webb)
                for t in ("Så mycket hade Konrad bokfört själv", "Uppskattning", "uppskattning, inget löfte",
                          'href="/konrad/"', "Läs om Konrad", "Om AI:", "Minuter per verifikation", "Ditt timpris"):
                    self.assertIn(t, ut)

    def test_okand_variant_stoppas(self):
        bok = g.las_sie(str(ROT / "exempel-sie.txt"))
        with self.assertRaises(ValueError):
            r.bygg(bok, [], IDAG, variant="Byrå")

    def test_byrasidan_namner_inte_konrad(self):
        self.assertNotIn("konrad", (ROT / "byra" / "index.html").read_text(encoding="utf-8").lower())
        self.assertNotIn("konrad", (ROT / "verktyg" / "byra_sida.py").read_text(encoding="utf-8").lower())

    def test_bara_startsidan_ber_om_gratisversionen(self):
        traffar = [p.relative_to(ROT).as_posix() for p in ROT.rglob("*")
                   if p.suffix in (".html", ".js", ".py") and p.is_file() and "webb=True, variant=\"gratis\"" in p.read_text(encoding="utf-8", errors="ignore")
                   and not p.relative_to(ROT).as_posix().startswith(("tester/", "pyodide/", ".git/"))]
        self.assertEqual(traffar, ["index.html"])


class Startsidan(unittest.TestCase):
    def setUp(self):
        self.html = (ROT / "index.html").read_text(encoding="utf-8")

    def test_motorn_laddar_modulen_och_samma_formel(self):
        self.assertIn('"konrad_andel.py"', self.html)
        self.assertEqual(self.html.count('webb=True, variant="gratis"'), 1)
        self.assertIn(ka.SKRIPT_JS, self.html)  # samma räkneformel i webbläsaren som i Python

    def test_exempelrapporten_ar_byggd_med_aktuell_kod(self):
        d = json.loads((ROT / "exempelrapport.json").read_text(encoding="utf-8"))
        gammal = n.SCB_FIL
        with tempfile.TemporaryDirectory() as tmp:
            n.SCB_FIL = str(Path(tmp) / "b.json"); shutil.copy(ROT / "scb" / "70.json", n.SCB_FIL)
            try:
                bok = g.las_sie(str(ROT / "exempel-sie.txt"))
                css, html = r.bygg(bok, g.granska(bok, IDAG), IDAG, "70.220", webb=True, variant="gratis")
            finally:
                n.SCB_FIL = gammal
        self.assertEqual((css, html), (d["css"], d["html"]))
        self.assertIn("58 av 95", html)
        self.assertIn("4,8 timmar", html)

    @unittest.skipUnless(shutil.which("node"), "node saknas")
    def test_js_formeln_ger_samma_svar(self):
        """Kör webbläsarens konradRakna() i node med låtsade fält och jämför med tid()."""
        for auto, minuter, timpris in ((58, "5", "600"), (58, "7,5", "450"), (6, "3", ""), (8, "10", "1 200")):
            js = ka.SKRIPT_JS + """
var f={'konrad-andel':{getAttribute:function(){return '%d';}},'konrad-min':{value:'%s'},'konrad-timpris':{value:'%s'},
'konrad-uttryck':{innerHTML:''},'konrad-kronor':{textContent:''}};
konradRakna({getElementById:function(i){return f[i];}});
console.log(JSON.stringify([f['konrad-uttryck'].innerHTML,f['konrad-kronor'].textContent]));""" % (auto, minuter, timpris)
            ut, kr = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
            m = float(minuter.replace(",", ".")); p = float(timpris.replace(" ", "")) if timpris else None
            t = ka.tid(auto, m, p)
            timmar = ka._dec(t["timmar"])
            self.assertIn(f"{timmar} timmar", ut.replace("\u00a0", " "))
            if p:
                self.assertIn(f"= {t['kronor']:,} kr".replace(",", " "), kr.replace("\u00a0", " "))
            else:
                self.assertIn("Fyll i ditt eget timpris", kr)


if __name__ == "__main__":
    unittest.main()
