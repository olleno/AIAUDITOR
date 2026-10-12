"""Karuseller för Kansliet och AI Auditor – reklambyråstil.

Varje sida väljer sin egen layout, så att en karusell aldrig ser likadan ut sida efter sida.
Gör PNG (1080x1350, LinkedIn/Instagram) och en PDF (LinkedIn-dokumentkarusell).

Användning: python3 karusell.py innehall.json utmapp

Layouter ("layout" på varje sida):
  foto       – helfoto med rubrik.            nycklar: bild, rubrik, text, markera
  delad      – foto ovan, text nedan.          nycklar: bild, rubrik, text
  kvitto     – kvittoremsa med rader.          nycklar: rader [[vänster, höger]], summa, notis, rubrik
  lapp       – handskriven gul lapp på bord.   nycklar: bild, lapp, under
  dagordning – stämmoprotokoll med paragrafer. nycklar: rubrik, punkter [[§, text, tid]], markerad, kommentar
  stampel    – foto med röd stämpel.           nycklar: bild, stampel, rubrik, text
  chatt      – två pratbubblor.                nycklar: rubrik, bubblor [[vem, text]]
  serif      – stor tidningsrubrik i serif.    nycklar: rubrik, text, kalla
Ord inom *stjärnor* i rubriker får ett rött penndrag (använd sparsamt, högst en sida per karusell).
"""
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageFilter

W, H = 1080, 1350
M = 96

FARG = {
    "text": "#141A16", "gron": "#4E7A45", "morkgron": "#1E3A31", "papper": "#F4F3EF",
    "sek": "#4A524D", "dampad": "#6B726E", "linje": "#C4C9C5", "ljusgron": "#8DB57F",
    "penna": "#C8372D", "lapp": "#F3DD7A", "kvitto": "#FBFAF6",
}

HAR = Path(__file__).parent
TYPS = HAR / "typsnitt"
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"


def inter(vikt, s):
    return ImageFont.truetype(INTER.format(vikt), s)


def serif(s, kursiv=False):
    return ImageFont.truetype(str(TYPS / ("Newsreader-SemiBoldItalic.ttf" if kursiv else "Newsreader-SemiBold.ttf")), s)


def mono(s, fet=False):
    return ImageFont.truetype(str(TYPS / ("PlexMono-SemiBold.ttf" if fet else "PlexMono-Medium.ttf")), s)


def hand(s):
    return ImageFont.truetype(str(TYPS / "Caveat-Bold.ttf"), s)


# ---------- hjälpfunktioner ----------

def radbryt(d, text, font, bredd):
    rader = []
    for stycke in text.split("\n"):
        rad = ""
        for o in stycke.split():
            prov = (rad + " " + o).strip()
            if d.textlength(prov, font=font) <= bredd:
                rad = prov
            else:
                if rad:
                    rader.append(rad)
                rad = o
        rader.append(rad)
    return rader


def penndrag(d, x0, x1, y, tj, fro):
    r = random.Random(fro)
    pts = []
    for i in range(15):
        t = i / 14
        pts.append((x0 - 6 + (x1 - x0 + 16) * t,
                    y + math.sin(t * 3.1 + r.random()) * tj * 0.35 + (t - 0.5) * tj * 0.5))
    d.line(pts, fill=FARG["penna"], width=tj, joint="curve")
    d.line([(px + 3, py + tj * 0.55) for px, py in pts[2:-1]], fill=FARG["penna"], width=max(2, tj // 2), joint="curve")


def skriv(d, xy, text, font, fill, bredd, rad=1.2, maxrader=None):
    """Radbryter. Ord inom *stjärnor* får rött penndrag."""
    x, y = xy
    ren = text.replace("*", "")
    rader = radbryt(d, ren, font, bredd)
    if maxrader and len(rader) > maxrader:
        raise ValueError(f"För lång text ({len(rader)} rader > {maxrader}): {ren[:50]}")
    flaggor = []
    for i, del_ in enumerate(text.split("*")):
        flaggor += [i % 2 == 1] * len(del_.split())
    k = 0
    for r in rader:
        d.text((x, y), r, font=font, fill=fill)
        cx = x
        for o in r.split():
            w = d.textlength(o, font=font)
            if k < len(flaggor) and flaggor[k]:
                penndrag(d, cx, cx + w, y + font.size * 1.05, max(4, font.size // 11), k * 31)
            cx += w + d.textlength(" ", font=font)
            k += 1
        y += int(font.size * rad)
    return y


def foto(namn, w=W, h=H, farg=0.6, ljus=1.0):
    f = Image.open(HAR / "bilder" / namn).convert("RGB")
    s = max(w / f.width, h / f.height)
    f = f.resize((int(f.width * s) + 1, int(f.height * s) + 1), Image.LANCZOS)
    vx, vy = (f.width - w) // 2, (f.height - h) // 2
    f = f.crop((vx, vy, vx + w, vy + h))
    f = ImageEnhance.Color(f).enhance(farg)
    return ImageEnhance.Brightness(f).enhance(ljus)


def tona(bild, farg, fran=140, till=235):
    ton = Image.new("RGB", bild.size, farg)
    mask = Image.new("L", bild.size)
    md = ImageDraw.Draw(mask)
    for y in range(bild.height):
        md.line([(0, y), (bild.width, y)], fill=int(fran + (till - fran) * y / bild.height))
    return Image.composite(ton, bild, mask)


def skugga(bas, lager, xy, radie=18, forskj=(10, 14), styrka=110):
    sk = Image.new("RGBA", lager.size, (0, 0, 0, styrka))
    alfa = lager.split()[-1] if lager.mode == "RGBA" else None
    if alfa:
        sk.putalpha(alfa.point(lambda a: styrka if a else 0))
    pad = radie * 3
    ram = Image.new("RGBA", (lager.width + pad * 2, lager.height + pad * 2), (0, 0, 0, 0))
    ram.paste(sk, (pad, pad), sk)
    ram = ram.filter(ImageFilter.GaussianBlur(radie))
    bas.paste(ram, (xy[0] - pad + forskj[0], xy[1] - pad + forskj[1]), ram)
    bas.paste(lager, xy, lager if lager.mode == "RGBA" else None)


# ---------- loggor och sidfot ----------

def logga_kansliet(d, x, y, s=1.0, morkt=False):
    t = FARG["papper"] if morkt else FARG["text"]
    sw = max(2, int(2 * s))
    d.rectangle([x, y, x + 40 * s, y + 40 * s], outline=t, width=sw)
    d.line([x, y + 15 * s, x + 40 * s, y + 15 * s], fill=t, width=sw)
    d.line([x + 22 * s, y, x + 22 * s, y + 40 * s], fill=t, width=sw)
    d.rectangle([x + 22 * s + sw, y + 15 * s + sw, x + 40 * s - sw + 1, y + 40 * s - sw + 1], fill=FARG["gron"])
    d.text((x + 56 * s, y - 4 * s), "KANSLIET", font=serif(int(28 * s)), fill=t)
    d.text((x + 57 * s, y + 27 * s), "POWERED BY NORDWIK PARTNERS", font=mono(int(9 * s)), fill=FARG["ljusgron"] if morkt else FARG["gron"])


def logga_aiauditor(d, x, y, s=1.0, morkt=False):
    s *= 0.9
    mork = FARG["papper"] if morkt else FARG["morkgron"]
    ljus = "#7C847F" if morkt else "#A9B0AB"
    gron = FARG["ljusgron"] if morkt else FARG["gron"]
    P = lambda a, b: (x + a * s, y + b * s)
    w3, w4 = max(2, int(3 * s)), max(3, int(4 * s))
    for pts in [[P(6, 17), P(6, 7), P(16, 7)], [P(40, 7), P(50, 7), P(50, 17)],
                [P(50, 39), P(50, 49), P(40, 49)], [P(16, 49), P(6, 49), P(6, 39)]]:
        d.line(pts, fill=mork, width=w3, joint="curve")
    d.line([P(15, 19), P(41, 19)], fill=ljus, width=w3)
    d.line([P(15, 28), P(35, 28)], fill=gron, width=w4)
    d.line([P(15, 37), P(41, 37)], fill=ljus, width=w3)
    cx, cy = P(41, 28)
    r = 3.5 * s
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=gron)
    f = inter("ExtraBold", int(27 * s))
    d.text(P(64, 32), "AI", font=f, fill=gron, anchor="ls")
    d.text(P(98, 32), "AUDITOR", font=f, fill=mork, anchor="ls")
    d.text(P(65, 48), "GRANSKNING AV BOKFÖRING", font=mono(max(8, int(9 * s))), fill=gron, anchor="ls")


def sidfot(d, varumarke, nr, antal, morkt=False, linje=True):
    farg = "#A3ACA6" if morkt else FARG["dampad"]
    if linje:
        d.line([M, H - 150, W - M, H - 150], fill="#3A5449" if morkt else FARG["linje"], width=2)
    if varumarke == "kansliet":
        logga_kansliet(d, M, H - 108, 1.0, morkt)
    else:
        logga_aiauditor(d, M - 6, H - 116, 1.2, morkt)
    t = f"{nr:02d} / {antal:02d}"
    d.text((W - M - d.textlength(t, font=mono(22)), H - 96), t, font=mono(22), fill=farg)


# ---------- layouter ----------

def l_foto(s, v, nr, n):
    img = tona(foto(s["bild"]), FARG["morkgron"], 120, 240)
    d = ImageDraw.Draw(img)
    f = inter("ExtraBold", s.get("storlek", 100))
    rader = radbryt(d, s["rubrik"].replace("*", ""), f, W - 2 * M)
    hojd = len(rader) * int(f.size * 1.05)
    textfont = inter("Regular", 36)
    th = len(radbryt(d, s.get("text", ""), textfont, W - 2 * M)) * 48 if s.get("text") else 0
    y = H - 210 - th - 40 - hojd
    y = skriv(d, (M, y), s["rubrik"], f, FARG["papper"], W - 2 * M, 1.05)
    if s.get("text"):
        skriv(d, (M, y + 30), s["text"], textfont, "#D3DBD5", W - 2 * M, 1.35)
    sidfot(d, v, nr, n, morkt=True)
    return img


def l_delad(s, v, nr, n):
    img = Image.new("RGB", (W, H), FARG["papper"])
    img.paste(foto(s["bild"], W, 700, farg=0.7), (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 700, W, 712], fill=FARG["gron"])
    y = skriv(d, (M, 770), s["rubrik"], inter("ExtraBold", s.get("storlek", 84)), FARG["text"], W - 2 * M, 1.05, 4)
    if s.get("text"):
        skriv(d, (M, y + 24), s["text"], inter("Regular", 34), FARG["sek"], W - 2 * M, 1.4, 3)
    sidfot(d, v, nr, n)
    return img


def l_kvitto(s, v, nr, n):
    img = Image.new("RGB", (W, H), "#2A332D")
    d = ImageDraw.Draw(img)
    if s.get("rubrik"):
        skriv(d, (M, 110), s["rubrik"], inter("ExtraBold", 54), FARG["papper"], W - 2 * M, 1.1, 2)
    # kvittoremsa med tandad underkant
    bw, x0, y0 = 760, (W - 760) // 2, 250
    rader = s["rader"]
    bh = 190 + len(rader) * 76 + 190
    rem = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rem)
    tand = 22
    poly = [(0, 0), (bw, 0), (bw, bh - tand)]
    for i in range(int(bw / tand), -1, -1):
        poly.append((i * tand, bh - (tand if i % 2 == 0 else 0)))
    rd.polygon(poly, fill=FARG["kvitto"])
    f, fb = mono(38), mono(40, True)
    rd.text((bw // 2, 54), s.get("titel", "AVSTÄMNING"), font=mono(30, True), fill=FARG["text"], anchor="mm")
    rd.text((bw // 2, 92), "- " * 26, font=mono(20), fill=FARG["dampad"], anchor="mm")
    y = 130
    for vtxt, htxt in rader:
        rd.text((44, y), vtxt, font=f, fill=FARG["text"])
        rd.text((bw - 44, y), htxt, font=f, fill=FARG["text"], anchor="ra")
        y += 76
    rd.text((bw // 2, y + 6), "- " * 26, font=mono(20), fill=FARG["dampad"], anchor="mm")
    if s.get("summa"):
        rd.text((44, y + 40), s["summa"][0], font=fb, fill=FARG["penna"])
        rd.text((bw - 44, y + 40), s["summa"][1], font=fb, fill=FARG["penna"], anchor="ra")
    rem = rem.rotate(-2.2, expand=True, resample=Image.BICUBIC)
    skugga(img, rem, (x0 - 10, y0))
    d = ImageDraw.Draw(img)
    if s.get("notis"):
        # handskriven anteckning i marginalen med pil
        nf = hand(84)
        nx, ny = M, y0 + bh + 70
        rader_n = radbryt(d, s["notis"], nf, W - 2 * M + 20)
        for i, r in enumerate(rader_n):
            d.text((nx, ny + i * 84), r, font=nf, fill="#F4C3BA")
    sidfot(d, v, nr, n, morkt=True, linje=False)
    return img


def l_lapp(s, v, nr, n):
    img = foto(s["bild"], farg=0.3, ljus=0.42) if s.get("bild") else Image.new("RGB", (W, H), "#3B3A36")
    lw, lh = 760, 760
    lapp = Image.new("RGBA", (lw, lh), FARG["lapp"])
    ld = ImageDraw.Draw(lapp)
    ld.rectangle([0, 0, lw, 70], fill="#EDD263")
    skriv(ld, (60, 120), s["lapp"], hand(s.get("storlek", 84)), "#2B2B2B", lw - 120, 1.08, 8)
    lapp = lapp.rotate(3.5, expand=True, resample=Image.BICUBIC)
    skugga(img, lapp, ((W - lapp.width) // 2, 150), radie=22, forskj=(14, 22), styrka=150)
    d = ImageDraw.Draw(img)
    if s.get("under"):
        band = Image.new("RGBA", (W, H - 960), (20, 30, 25, 225))
        img.paste(band, (0, 960), band)
        d = ImageDraw.Draw(img)
        skriv(d, (M, 1000), s["under"], inter("SemiBold", 36), FARG["papper"], W - 2 * M, 1.35, 3)
    sidfot(d, v, nr, n, morkt=True)
    return img


def l_dagordning(s, v, nr, n):
    img = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(img)
    # linjerat protokollspapper
    for y in range(260, H - 180, 58):
        d.line([0, y, W, y], fill="#E3E8EF", width=2)
    d.line([M + 70, 0, M + 70, H], fill="#EBC3BE", width=3)
    d.text((M + 100, 110), s.get("rubrik", "Dagordning"), font=serif(64), fill=FARG["text"])
    d.text((M + 100, 196), s.get("underrubrik", ""), font=mono(24), fill=FARG["dampad"])
    y = 276
    for i, (par, txt, tid) in enumerate(s["punkter"]):
        f = inter("Medium", 34)
        d.text((M + 100, y), par, font=mono(30), fill=FARG["dampad"])
        d.text((M + 190, y), txt, font=f, fill=FARG["text"])
        d.text((W - M, y), tid, font=mono(30, True), fill=FARG["text"], anchor="ra")
        if i == s.get("markerad"):
            # handritad ring runt punkten
            r = random.Random(7)
            box = [M + 170, y - 18, W - M + 24, y + 58]
            pts = []
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            rx, ry = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
            for k in range(60):
                a = 2 * math.pi * k / 56 - 0.4
                pts.append((cx + rx * math.cos(a) * (1 + r.uniform(-0.01, 0.02)), cy + ry * math.sin(a) * (1 + r.uniform(-0.04, 0.06))))
            d.line(pts, fill=FARG["penna"], width=6, joint="curve")
        y += 116
    if s.get("kommentar"):
        d.text((M + 100, y + 10), s["kommentar"], font=hand(70), fill=FARG["penna"])
    sidfot(d, v, nr, n, linje=False)
    return img


def l_stampel(s, v, nr, n):
    img = tona(foto(s["bild"], farg=0.5), "#F3F0E9", 175, 235)
    d = ImageDraw.Draw(img)
    # stämpel
    st = Image.new("RGBA", (760, 260), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([10, 10, 750, 250], radius=24, outline=FARG["penna"], width=12)
    sd.rounded_rectangle([30, 30, 730, 230], radius=14, outline=FARG["penna"], width=4)
    sd.text((380, 130), s["stampel"], font=inter("Black", 110), fill=FARG["penna"], anchor="mm")
    # slitet bläck
    r = random.Random(3)
    px = st.load()
    for _ in range(9000):
        x, y = r.randrange(760), r.randrange(260)
        if px[x, y][3]:
            px[x, y] = (0, 0, 0, 0)
    st = st.rotate(-9, expand=True, resample=Image.BICUBIC)
    img.paste(st, ((W - st.width) // 2, 200), st)
    y = skriv(d, (M, 640), s["rubrik"], inter("ExtraBold", s.get("storlek", 80)), FARG["text"], W - 2 * M, 1.05, 4)
    if s.get("text"):
        skriv(d, (M, y + 30), s["text"], inter("Regular", 36), FARG["sek"], W - 2 * M, 1.4, 4)
    sidfot(d, v, nr, n)
    return img


def l_chatt(s, v, nr, n):
    img = Image.new("RGB", (W, H), "#E9EEE7")
    d = ImageDraw.Draw(img)
    if s.get("rubrik"):
        skriv(d, (M, 110), s["rubrik"], mono(28, True), FARG["gron"], W - 2 * M, 1.3, 2)
    y = 240
    for vem, txt in s["bubblor"]:
        hoger = vem != s["bubblor"][0][0]
        f = inter("Medium", 40)
        rader = radbryt(d, txt, f, 600)
        bw = max(d.textlength(r, font=f) for r in rader) + 80
        bh = len(rader) * 54 + 60
        x = W - M - bw if hoger else M
        fyll = FARG["morkgron"] if hoger else "#FFFFFF"
        tf = FARG["papper"] if hoger else FARG["text"]
        d.text((x + (bw if hoger else 0), y), vem, font=mono(22), fill=FARG["dampad"], anchor="ra" if hoger else "la")
        y += 36
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=34, fill=fyll)
        for i, r in enumerate(rader):
            d.text((x + 40, y + 30 + i * 54), r, font=f, fill=tf)
        y += bh + 50
    sidfot(d, v, nr, n)
    return img


def l_serif(s, v, nr, n):
    img = Image.new("RGB", (W, H), FARG["papper"])
    d = ImageDraw.Draw(img)
    d.text((W - 40, H - 120), s.get("dekor", "§"), font=serif(760), fill="#E2E6DC", anchor="rs")
    d.text((M, 120), s.get("etikett", "").upper(), font=mono(24, True), fill=FARG["gron"])
    y = skriv(d, (M, 200), s["rubrik"], serif(s.get("storlek", 104), kursiv=s.get("kursiv", False)), FARG["text"], W - 2 * M, 1.02, 6)
    if s.get("text"):
        skriv(d, (M, y + 40), s["text"], inter("Regular", 36), FARG["sek"], W - 2 * M, 1.4, 6)
    if s.get("kalla"):
        d.text((M, H - 200), "Källa: " + s["kalla"], font=inter("Medium", 22), fill=FARG["dampad"])
    sidfot(d, v, nr, n)
    return img


LAYOUTER = {"foto": l_foto, "delad": l_delad, "kvitto": l_kvitto, "lapp": l_lapp,
            "dagordning": l_dagordning, "stampel": l_stampel, "chatt": l_chatt, "serif": l_serif}


def bygg(json_fil, utmapp):
    data = json.loads(Path(json_fil).read_text(encoding="utf-8"))
    v = data["varumarke"]
    assert v in ("kansliet", "aiauditor")
    sidor = data["sidor"]
    layouter = [s["layout"] for s in sidor]
    if len(set(layouter)) < len(layouter):
        raise ValueError("Samma layout används två gånger i samma karusell – variera.")
    if sum("*" in s.get("rubrik", "") + s.get("lapp", "") for s in sidor) > 1:
        raise ValueError("Rött penndrag på mer än en sida – högst en per karusell.")
    ut = Path(utmapp)
    ut.mkdir(parents=True, exist_ok=True)
    bilder = []
    for i, s in enumerate(sidor, 1):
        img = LAYOUTER[s["layout"]](s, v, i, len(sidor)).convert("RGB")
        img.save(ut / f"sida-{i:02d}.png")
        bilder.append(img)
    bilder[0].save(ut / "karusell.pdf", save_all=True, append_images=bilder[1:], resolution=150)
    return [str(p) for p in sorted(ut.glob("sida-*.png"))] + [str(ut / "karusell.pdf")]


if __name__ == "__main__":
    for p in bygg(sys.argv[1], sys.argv[2]):
        print(p)
