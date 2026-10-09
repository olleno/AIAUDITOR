#!/usr/bin/env python3
"""Utläggaren – publicerar godkända inlägg på Instagram.

Körs var 15:e minut på servern (systemd-timer). Hämtar kön från
https://aiauditor.se/media/ko.json. Ett inlägg publiceras bara om
  - "godkand" är true (Olle har sagt ja),
  - "publicera_efter" har passerats,
  - det inte redan är publicerat (se /opt/redaktionen/publicerat.json).
Nycklarna läses från /opt/redaktionen/.env (IG_TOKEN_KANSLIET, IG_TOKEN_AIAUDITOR).

Strömbrytare: finns filen /opt/redaktionen/STOPP gör den ingenting.
Max 2 publiceringar per körning, som skydd mot att något skenar.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HEM = Path(os.environ.get("REDAKTION_HEM", "/opt/redaktionen"))
KO_URL = os.environ.get("KO_URL", "https://aiauditor.se/media/ko.json")
API = "https://graph.instagram.com/v21.0"
MAX_PER_KORNING = 2
KONTON = {"kansliet": "IG_TOKEN_KANSLIET", "aiauditor": "IG_TOKEN_AIAUDITOR"}


def logg(t):
    rad = f"{dt.datetime.now().isoformat(timespec='seconds')} {t}"
    print(rad, flush=True)
    with open(HEM / "logg.txt", "a", encoding="utf-8") as f:
        f.write(rad + "\n")


def las_env():
    env = {}
    for rad in (HEM / ".env").read_text().splitlines():
        if "=" in rad:
            k, v = rad.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def hamta(url):
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + f"t={int(time.time())}",
                                 headers={"User-Agent": "kansliet-redaktion"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def anrop(metod, sokvag, data, token):
    data = dict(data, access_token=token)
    body = urllib.parse.urlencode(data).encode()
    url = f"{API}/{sokvag}"
    if metod == "GET":
        req = urllib.request.Request(url + "?" + body.decode())
    else:
        req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        fel = e.read().decode()[:400]
        raise RuntimeError(f"Instagram svarade {e.code}: {fel}") from None


def vanta_klar(container_id, token, max_s=120):
    for _ in range(max_s // 5):
        s = anrop("GET", container_id, {"fields": "status_code"}, token).get("status_code")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram kunde inte läsa bilden (status {s})")
        time.sleep(5)
    raise RuntimeError("Instagram blev inte klar i tid")


def publicera(post, token):
    if post.get("typ") == "reel":
        c = anrop("POST", "me/media", {"media_type": "REELS", "video_url": post["video"],
                                         "caption": post["text"], "share_to_feed": "true"}, token)["id"]
        vanta_klar(c, token, max_s=600)
        return anrop("POST", "me/media_publish", {"creation_id": c}, token)["id"]
    bilder = post["bilder"]
    if not 1 <= len(bilder) <= 10:
        raise ValueError("En karusell måste ha 1–10 bilder")
    if len(bilder) == 1:
        c = anrop("POST", "me/media", {"image_url": bilder[0], "caption": post["text"]}, token)["id"]
    else:
        barn = []
        for b in bilder:
            barn.append(anrop("POST", "me/media", {"image_url": b, "is_carousel_item": "true"}, token)["id"])
        for b in barn:
            vanta_klar(b, token)
        c = anrop("POST", "me/media", {"media_type": "CAROUSEL", "children": ",".join(barn),
                                         "caption": post["text"]}, token)["id"]
    vanta_klar(c, token)
    return anrop("POST", "me/media_publish", {"creation_id": c}, token)["id"]


def main():
    if (HEM / "STOPP").exists() or os.environ.get("REDAKTION_STOPP") == "1":
        logg("STOPP är satt – gör ingenting.")
        return 0
    gjort_fil = HEM / "publicerat.json"
    gjort = json.loads(gjort_fil.read_text()) if gjort_fil.exists() else {}
    try:
        ko = hamta(KO_URL)
    except Exception as e:  # källan svarar inte → gör ingenting
        logg(f"Kunde inte hämta kön: {e}")
        return 0
    env = las_env()
    nu = dt.datetime.now(dt.timezone.utc)
    antal = 0
    for post in ko.get("inlagg", []):
        pid = post["id"]
        if pid in gjort or not post.get("godkand") or post.get("kanal") != "instagram":
            continue
        efter = dt.datetime.fromisoformat(post.get("publicera_efter", "2000-01-01T00:00:00+00:00"))
        if efter > nu:
            continue
        if antal >= MAX_PER_KORNING:
            logg("Max antal per körning nått, resten tas nästa gång.")
            break
        token = env.get(KONTON.get(post["konto"], ""), "")
        if not token:
            logg(f"{pid}: ingen nyckel för konto {post['konto']}")
            continue
        try:
            media_id = publicera(post, token)
            gjort[pid] = {"media_id": media_id, "tid": nu.isoformat(timespec="seconds"), "konto": post["konto"]}
            gjort_fil.write_text(json.dumps(gjort, indent=1, ensure_ascii=False))
            logg(f"{pid}: PUBLICERAD på {post['konto']} (media {media_id})")
            antal += 1
        except Exception as e:
            logg(f"{pid}: FEL – {e}")
    if antal == 0:
        logg("Inget att publicera.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
