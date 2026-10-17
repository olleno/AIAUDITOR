"""Tester för AI-sökpaketet på aiauditor.se. Körs från repots rot efter bygget:

    python3 verktyg/bygg_sidor.py && python3 -m unittest discover -s tester -p 'aiauditor_test_*.py'

Kontrollerar: JSON-LD finns och är giltigt, llms.txt och llms-full.txt, robots.txt släpper in AI-botarna,
sajtkartan, att API-flödena validerar mot OpenAPI-schemat, frågebanken, enhetliga avsändaruppgifter,
datum på sidorna och fabrikskollens regler (inga förbjudna ord, inga betyg)."""
import html, json, re, sys, unittest
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROT / "verktyg"))
import aiauditor_fakta as F  # noqa: E402

FABRIK = Path.home() / "verket" / "fabrik"
# Sidor som medvetet inte indexeras: Konrad (ej släppt), kontosidan och omdirigeringen /conrad/ -> /konrad/.
NOINDEX = {"konrad/index.html", "konrad/villkor/index.html", "konrad/logga-in/index.html", "konto/index.html", "conrad/index.html"}
UTESLUTS = ("media/", "redaktionen/", "pyodide/", "typsnitt/", ".git/")
AI_BOTAR = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot",
            "PerplexityBot", "Google-Extended", "Bingbot", "Applebot-Extended"]
TYPER = {"Organization", "WebSite", "WebApplication", "Offer", "FAQPage", "Question", "Answer", "BreadcrumbList", "ListItem",
         "Dataset", "DataDownload", "HowTo", "HowToStep"}
FORBJUDNA = re.compile(r"\b(bäst i test|testvinnare|vårt val|mest populär\w*|populärast\w*|topprankad\w*|nummer ett|#1 i sverige|"
                       r"mest klickad\w*|officiell vinnare|bästa\b|bäst\b|vi rekommenderar)", re.I)
DATUM = re.compile(r"(Uppdaterad|uppdaterad|kontrollerad\w*|Kontrollerad\w*|hämtad|Hämtad)[^<]{0,40}\d{4}-\d{2}-\d{2}|20\d\d-\d\d-\d\d")


def sidor():
    for p in sorted(ROT.rglob("index.html")):
        rel = p.relative_to(ROT).as_posix()
        if not rel.startswith(UTESLUTS): yield rel, p.read_text(encoding="utf-8", errors="ignore")


def indexerade():
    return [(r, h) for r, h in sidor() if r not in NOINDEX]


def text(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def ld(h):
    return [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)]


def noder(x):
    if isinstance(x, list):
        for y in x: yield from noder(y)
    elif isinstance(x, dict):
        if "@type" in x: yield x
        for v in x.values(): yield from noder(v)


def validera(v, s, schemas, sti="$"):
    """Liten JSON-schema-validator (type, required, properties, items, enum, pattern, additionalProperties, $ref)."""
    if "$ref" in s: s = schemas[s["$ref"].split("/")[-1]]
    t = s.get("type")
    if t:
        ok = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "null": type(None), "boolean": bool}
        tt = t if isinstance(t, list) else [t]
        if not any(isinstance(v, ok[x]) and not (x in ("integer", "number") and isinstance(v, bool)) for x in tt):
            raise AssertionError(f"{sti}: {v!r} är inte {t}")
    if "enum" in s and v not in s["enum"]: raise AssertionError(f"{sti}: {v!r} inte i {s['enum']}")
    if "pattern" in s and isinstance(v, str) and not re.search(s["pattern"], v): raise AssertionError(f"{sti}: {v!r} matchar inte {s['pattern']}")
    if isinstance(v, dict):
        for k in s.get("required", []):
            if k not in v: raise AssertionError(f"{sti}: saknar {k}")
        for k, x in v.items():
            if k in s.get("properties", {}): validera(x, s["properties"][k], schemas, f"{sti}.{k}")
            elif isinstance(s.get("additionalProperties"), dict): validera(x, s["additionalProperties"], schemas, f"{sti}.{k}")
    if isinstance(v, list) and "items" in s:
        for i, x in enumerate(v): validera(x, s["items"], schemas, f"{sti}[{i}]")


class JsonLd(unittest.TestCase):
    def test_varje_indexerad_sida_har_giltigt_jsonld(self):
        for rel, h in indexerade():
            block = ld(h)
            self.assertTrue(block, f"{rel}: saknar JSON-LD")
            for b in block:
                self.assertEqual(b.get("@context") if isinstance(b, dict) else b[0].get("@context"), "https://schema.org", rel)
                for n in noder(b):
                    self.assertIn(n["@type"], TYPER, f"{rel}: okänd eller otillåten typ {n['@type']}")

    def test_organization_och_website_overallt_och_enhetligt(self):
        for rel, h in indexerade():
            org = [n for b in ld(h) for n in noder(b) if n["@type"] == "Organization" and n.get("@id")]
            self.assertTrue(org, f"{rel}: saknar Organization")
            self.assertEqual(org[0]["name"], F.AVSANDARE, rel)
            self.assertEqual(org[0]["taxID"], F.ORGNR, rel)
            self.assertTrue(any(n["@type"] == "WebSite" for b in ld(h) for n in noder(b)), f"{rel}: saknar WebSite")

    def test_inga_betyg_eller_recensioner(self):
        for rel, h in sidor():
            for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
                self.assertNotRegex(s, r'"(Review|AggregateRating)"|"aggregateRating"|"review"', rel)

    def test_faq_bara_med_synliga_fragor(self):
        for rel, h in indexerade():
            t = text(h)
            for n in (n for b in ld(h) for n in noder(b) if n["@type"] == "Question"):
                self.assertIn(n["name"].rstrip("?"), t, f"{rel}: FAQ-frågan syns inte på sidan: {n['name']}")

    def test_dataset_har_kalla_licens_och_flode(self):
        n = 0
        for rel, h in indexerade():
            for d in (d for b in ld(h) for d in noder(b) if d["@type"] == "Dataset"):
                n += 1
                for k in ("name", "description", "creator", "license", "temporalCoverage", "url", "distribution"):
                    self.assertIn(k, d, f"{rel}: Dataset saknar {k}")
        self.assertGreater(n, 800)

    def test_brodsmulor_numrerade(self):
        for rel, h in indexerade():
            for b in (n for x in ld(h) for n in noder(x) if n["@type"] == "BreadcrumbList"):
                self.assertEqual([i["position"] for i in b["itemListElement"]], list(range(1, len(b["itemListElement"]) + 1)), rel)


class LlmsOchRobots(unittest.TestCase):
    def test_llms_txt(self):
        t = (ROT / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(t.startswith("# AI Auditor\n"))
        self.assertNotIn("<html", t.lower())
        for s in ("/api/v1/openapi.json", "/api/v1/branscher.json", "/api/v1/kontroller.json", "/llms-full.txt", "/kontroller/", F.AVSANDARE, F.ORGNR, F.EPOST):
            self.assertIn(s, t)
        self.assertNotIn("/konrad", t, "Konrad är inte släppt för sökmotorer")
        kon = json.loads((ROT / "api/v1/kontroller.json").read_text())
        self.assertIn(f"alla {kon['antal']} aktiva kontroller", t)
        self.assertIn(f"alla {json.loads((ROT / 'api/v1/branscher.json').read_text())['antal']} branscher", t)

    def test_llms_full_txt(self):
        t = (ROT / "llms-full.txt").read_text(encoding="utf-8")
        self.assertTrue(t.startswith("# AI Auditor"))
        self.assertNotIn("<html", t.lower())
        for k in json.loads((ROT / "api/v1/kontroller.json").read_text())["kontroller"]:
            self.assertIn(k["id"] + " ", t)

    def test_llms_lankar_finns(self):
        for u in re.findall(r"\]\(https://aiauditor\.se(/[^)]*)\)", (ROT / "llms.txt").read_text()):
            p = ROT / u.lstrip("/")
            self.assertTrue((p / "index.html").exists() if u.endswith("/") else p.exists(), u)

    def test_robots_slapper_in_ai_botarna(self):
        r = (ROT / "robots.txt").read_text()
        for bot in AI_BOTAR:
            self.assertRegex(r, rf"(?m)^User-agent:\s*{re.escape(bot)}\s*\n(?:[^\n]+\n)*?Allow:\s*/\s*$", bot)
        self.assertIn("Disallow: /redaktionen/", r)
        self.assertIn("Sitemap: https://aiauditor.se/sitemap.xml", r)

    def test_sajtkartan_komplett(self):
        x = (ROT / "sitemap.xml").read_text()
        urls = re.findall(r"<url><loc>https://aiauditor\.se(/[^<]*)</loc><lastmod>\d{4}-\d{2}-\d{2}</lastmod></url>", x)
        self.assertEqual(len(urls), x.count("<url>"), "varje adress ska ha lastmod")
        self.assertLess(len(urls), 50000)
        sidorna = {"/" + r[:-len("index.html")] for r, _ in indexerade()}
        self.assertEqual(set(urls), sidorna)


class Flode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = json.loads((ROT / "api/v1/openapi.json").read_text())

    def test_flodena_validerar_mot_schemat(self):
        sch = self.api["components"]["schemas"]
        for vag, op in self.api["paths"].items():
            data = json.loads((ROT / "api/v1" / vag.lstrip("/")).read_text())
            validera(data, op["get"]["responses"]["200"]["content"]["application/json"]["schema"], sch, vag)

    def test_bara_lasande(self):
        for op in self.api["paths"].values():
            self.assertEqual(set(op), {"get"})

    def test_kalla_och_datum_per_post(self):
        b = json.loads((ROT / "api/v1/branscher.json").read_text())
        self.assertEqual(b["antal"], len(b["branscher"]))
        for x in b["branscher"]:
            self.assertTrue(x["kalla"].startswith("SCB") and x["hamtad"] == F.SCB_HAMTAD)
            self.assertTrue((ROT / x["url"].replace(F.SAJT + "/", "") / "index.html").exists(), x["url"])
        for x in json.loads((ROT / "api/v1/kontroller.json").read_text())["kontroller"]:
            self.assertTrue(x["kalla"] and x["senast_kontrollerad"])

    def test_inga_personuppgifter(self):
        for p in (ROT / "api/v1").glob("*.json"):
            t = p.read_text()
            self.assertNotRegex(t, r"\b\d{6,8}-\d{4}\b", f"{p.name}: person- eller organisationsnummer")
            self.assertNotRegex(t.replace(F.EPOST, ""), r"[\w.+-]+@[\w-]+\.[\w.]+", f"{p.name}: e-postadress")


class Fragebank(unittest.TestCase):
    def test_fragebanken(self):
        d = json.loads((ROT / "data/ai-fragor.json").read_text())
        f = d["fragor"]
        self.assertTrue(30 <= len(f) <= 50)
        self.assertEqual(d["antal"], len(f))
        self.assertEqual(d["antal_med_svarssida"], sum(1 for x in f if x["svarssida"]))
        for x in f:
            self.assertIn(x["avsikt"], d["avsikter"])
            if x["svarssida"]:
                p = ROT / x["svarssida"].replace(F.SAJT + "/", "") / "index.html"
                self.assertTrue(p.exists(), x["svarssida"])
                self.assertNotIn(p.relative_to(ROT).as_posix(), NOINDEX)
            else:
                self.assertEqual(x["status"], "saknar data")
                self.assertTrue(x["kommentar"])

    def test_matprotokoll(self):
        d = json.loads((ROT / "data/ai-synlighet.json").read_text())
        self.assertEqual(set(d["tjanster"]), {"ChatGPT", "Gemini", "Claude", "Perplexity", "Copilot"})
        self.assertEqual(d["klassning"], ["ej nämnd", "nämnd", "topp 3", "nr 1"])
        self.assertTrue(any("skrapning" in s for s in d["sa_gar_det_till"]))


class Fabriksregler(unittest.TestCase):
    def test_inga_forbjudna_ord(self):
        for rel, h in sidor():
            m = FORBJUDNA.search(text(h))
            self.assertIsNone(m, f"{rel}: förbjudet ord '{m.group(0) if m else ''}'")

    def test_datum_pa_indexerade_sidor(self):
        for rel, h in indexerade():
            self.assertRegex(text(h), DATUM, f"{rel}: saknar datum")

    def test_noindex_bara_dar_det_ska(self):
        for rel, h in sidor():
            self.assertEqual('name="robots" content="noindex' in h, rel in NOINDEX, rel)

    def test_enhetlig_avsandare_i_sidfoten(self):
        for rel, h in indexerade():
            if rel == "index.html": continue  # startsidan har egen sidfot med länk till /integritet/
            self.assertIn(F.AVSANDARE, text(h), rel)

    @unittest.skipUnless((FABRIK / "fabrikskoll.py").exists(), "fabriken saknas")
    def test_fabrikskoll_bara_kanda_undantag(self):
        """Fabrikskollen körs mot repot (som är sin egen public/). Kända undantag: noindex-sidorna ovan och
        e-postfälten på /konrad/ och /byra/ (inloggning och intresseanmälan som öppnar e-postprogrammet)."""
        import tempfile, os
        sys.path.insert(0, str(FABRIK))
        import fabrikskoll
        with tempfile.TemporaryDirectory(prefix="aiauditor_fk_") as d:
            os.symlink(ROT, Path(d) / "public"); (Path(d) / "build.py").write_text("")
            _, fel = fabrikskoll.kolla(d)
        kanda = re.compile(r"^(konrad|konto|conrad)/.*(saknar datum|noindex trots|e-postfält)|^byra/index\.html: e-postfält$")
        okanda = [f for f in fel if not kanda.search(f)]
        self.assertEqual(okanda, [])


if __name__ == "__main__":
    unittest.main()
