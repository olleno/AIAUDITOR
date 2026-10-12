# Redaktionen

Verktygen för Kansliets och AI Auditors inlägg.

- `karusell.py <inlägg.json> <utmapp>` ritar en bildserie (1080x1350 PNG + PDF). Layouter: foto, delad, kvitto, lapp, dagordning, stampel, chatt, serif. Samma layout får inte upprepas i en serie, högst ett rött penndrag (`*ord*`).
- `reel.py <mapp med sida-*.png> <film.mp4>` gör en kort film (1080x1920) av bildserien. Kräver ffmpeg.
- `utlaggare.py` körs på servern var 15:e minut och lägger ut det i `/media/ko.json` som har `"godkand": true`.
- Exempel på indata: `prov-kansliet.json`, `prov-aiauditor.json`.

Inlägg läggs i `/media/<id>/` (sida-01.jpg …, film.mp4) och i `/media/ko.json` med `"godkand": false`. Bara Olle säger ja.
