"""Tester för Konrad-sidorna på aiauditor.se/konrad/ (en sajt, noindex tills Olle släpper den).

    python3 verktyg/bygg_sidor.py && python3 -m unittest discover -s tester -p 'aiauditor_test_*.py'

Kontrollerar: noindex på alla Konrad-sidor, ingen Konrad i sajtkarta/llms/flöden, inga förbjudna fraser,
att priserna på sidan är samma som i data/konrad-priser.json (och i räknefunktionen kalkyl.js), att varje funktion i
"Det här ingår" finns i funktionsdatan med status "vid lansering", och att inga länkar pekar på konradredovisning.se."""
import html, json, re, subprocess, unittest
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
KONRAD = ROT / "konrad"
DATA = ROT / "konrad-kalla" / "data"
FORBJUDNA = ["bokför automatiskt", "allt automatiskt", "automatisk bokföring",
             "automatisk löpande bokföring", "bokför allt själv"]
MAN = re.compile(r"(populärast|mest populär|vanligaste valet|bäst i test|testvinnare)", re.I)


def sidor():
    return {p.relative_to(ROT).as_posix(): p.read_text(encoding="utf-8") for p in sorted(KONRAD.rglob("index.html"))}


def text(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def j(namn):
    return json.loads((DATA / f"{namn}.json").read_text(encoding="utf-8"))


def kr(n):
    return f"{n:,}".replace(",", " ") + " kr"


class KonradTest(unittest.TestCase):
    def test_sidorna_finns(self):
        self.assertEqual(set(sidor()), {f"konrad/{s}index.html" for s in
                         ["", "villkor/", "logga-in/", "trygghet/", "312-kalkylator-2026/", "vad-kostar-din-bokforing/"]})

    def test_noindex_pa_alla(self):
        for rel, h in sidor().items():
            self.assertIn('<meta name="robots" content="noindex,nofollow">', h, rel)
        c = (ROT / "conrad" / "index.html").read_text(encoding="utf-8")
        self.assertIn("noindex", c)

    def test_konrad_utanfor_sajtkarta_llms_floden(self):
        for f in ["sitemap.xml", "llms.txt", "llms-full.txt"] + [str(p.relative_to(ROT)) for p in (ROT / "api").rglob("*.json")]:
            self.assertNotIn("konrad", (ROT / f).read_text(encoding="utf-8").lower(), f)

    def test_inga_forbjudna_fraser(self):
        for rel, h in sidor().items():
            t = text(h).lower()
            for f in FORBJUDNA:
                self.assertNotIn(f, t, f"{rel}: {f}")
            self.assertIsNone(MAN.search(t), rel)
        for p in list((ROT / "konrad-kalla").rglob("*.*")) + list((KONRAD / "js").glob("*.js")):
            t = p.read_text(encoding="utf-8").lower()
            for f in ("bokför automatiskt", "allt automatiskt"):
                self.assertNotIn(f, t, f"{p}: {f}")

    def test_priserna_pa_sidan_ar_datafilens(self):
        P = j("konrad-priser")
        h = sidor()["konrad/index.html"]
        t = text(h)
        for n in P["nivaer"]:
            self.assertIn(f'<h3>{n["namn"]}</h3><div class="pris">{kr(n["pris"])}<small>', h)
        self.assertIn(f"Bokslut och årsredovisning: {kr(P['bokslut']['pris_ar'])} per år", t)
        for tv in P["tillval"]:
            self.assertIn(html.escape(tv["text"], quote=True), h)
            self.assertIn(f"<td>{html.escape(tv['pris'])}</td>", h)
        # nivåpriserna i texten ("Bevakning (199 kr)") ska också stämma
        for n in P["nivaer"][1:]:
            self.assertIn(f"{n['namn']} ({kr(n['pris'])})", t)

    def test_priserna_ar_oforandrade_mot_konrad_sajt(self):
        kalla = Path.home() / "verket" / "konrad-sajt" / "data" / "konrad-priser.json"
        if not kalla.exists():
            self.skipTest("konrad-sajt finns inte på den här datorn")
        K, P = json.loads(kalla.read_text(encoding="utf-8")), j("konrad-priser")
        self.assertEqual([(n["id"], n["pris"]) for n in K["nivaer"]], [(n["id"], n["pris"]) for n in P["nivaer"]])
        self.assertEqual(K["bokslut"]["pris_ar"], P["bokslut"]["pris_ar"])
        # tillvalen (avgiftsvaktens 20 % av besparingen ingår – beslutad prislista)
        self.assertEqual([t["pris"] for t in K["tillval"]], [t["pris"] for t in P["tillval"]])

    def test_rakneformeln_ger_datafilens_priser(self):
        P = j("konrad-priser")
        js = (KONRAD / "js" / "kalkyl.js").read_text(encoding="utf-8")
        script = ("const K=require(process.argv[1]);const o=[];"
                  "for(let n=0;n<5;n++){o.push(K.konradPris({niva:n,ver:0,bank:1,anst:0,del:1,bokslut:false}).perManad);}"
                  "o.push(K.konradPris({niva:0,ver:0,bank:1,anst:0,del:1,bokslut:true}).perAr);"
                  "console.log(JSON.stringify(o));")
        try:
            ut = subprocess.run(["node", "-e", script, str(KONRAD / "js" / "kalkyl.js")], capture_output=True, text=True, check=True).stdout
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.skipTest("node saknas")
        self.assertEqual(json.loads(ut), [n["pris"] for n in P["nivaer"]] + [P["bokslut"]["pris_ar"]])
        self.assertIn("NIVAPRIS = [" + ", ".join(str(n["pris"]) for n in P["nivaer"]) + "]", js)

    def test_det_har_ingar_ar_funktionsdatan(self):
        F = {f["id"]: f for f in j("funktioner")["funktioner"]}
        h = sidor()["konrad/index.html"]
        sek = re.search(r'<section class="band" id="ingar">.*?</section>', h, re.S).group(0)
        ids = re.findall(r'data-funktion="([^"]+)"', sek)
        self.assertEqual(sorted(ids), sorted(F))
        for i in ids:
            kort = re.search(r'<div data-funktion="%s">.*?</div>' % re.escape(i), sek, re.S).group(0)
            self.assertIn(html.escape(F[i]["namn"], quote=True), kort)
            self.assertIn(f'<span class="snart">{F[i]["status"]}</span>', kort)
            self.assertEqual(F[i]["status"], "vid lansering")

    def test_nya_avgifter_ar_markt_vid_lansering(self):
        h = sidor()["konrad/index.html"]
        m = re.search(r"<li>Nya avgifter du kanske inte har beställt.*?</li>", h, re.S).group(0)
        self.assertIn('<span class="snart">vid lansering</span>', m)

    def test_inga_lankar_till_konradredovisning(self):
        for rel, h in list(sidor().items()) + [(str(p), p.read_text(encoding="utf-8")) for p in (KONRAD / "js").glob("*.js")]:
            self.assertNotIn("konradredovisning", h, rel)

    def test_interna_lankar_pekar_pa_konrad_och_finns(self):
        s = sidor()
        for rel, h in s.items():
            for href in re.findall(r'(?:href|src)="(/[^"]*)"', h):
                if href == "/":
                    continue
                self.assertTrue(href.startswith("/konrad/"), f"{rel}: {href}")
                fil = ROT / href.split("#")[0].lstrip("/")
                self.assertTrue((fil / "index.html").exists() or fil.is_file(), f"{rel}: {href}")

    def test_granska_gratis_gar_till_granskningen(self):
        h = sidor()["konrad/index.html"]
        self.assertGreaterEqual(h.count('<a class="knapp" href="/">'), 1)
        self.assertIn('<a class="knapp" href="/">Granska din bokföring gratis</a>', h)
        self.assertIn("Bokföringen är gratis. Du betalar när vi gör jobbet åt dig.", h)

    def test_logga_in_utan_riktig_inloggning(self):
        h = sidor()["konrad/logga-in/index.html"]
        self.assertNotIn('type="email"', h)
        self.assertIn("vid lansering", h)

    def test_konrad_ar_ett_ai_system(self):
        t = text(sidor()["konrad/index.html"])
        self.assertIn("Konrad är vårt system, din AI-kamrer", t)


if __name__ == "__main__":
    unittest.main()
