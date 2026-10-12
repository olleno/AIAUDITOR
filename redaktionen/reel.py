"""Gör en kort stående film (Reel, 1080x1920) av en karusells bilder.
Varje bild visas ca 3 s med en långsam inzoomning, mjuk övertoning mellan bilderna.
Användning: python3 reel.py utmapp_med_sida-NN.png film.mp4"""
import subprocess, sys, glob, os
from PIL import Image, ImageFilter
src, ut = sys.argv[1], sys.argv[2]
sidor = sorted(glob.glob(os.path.join(src, "sida-*.png")))
tmp = ut + ".delar"; os.makedirs(tmp, exist_ok=True)
D, F = 3.2, 0.5  # sekunder per bild, övertoning
klipp = []
for i, s in enumerate(sidor):
    b = Image.open(s).convert("RGB")
    bg = b.resize((1080, 1350)).resize((1536, 1920)).crop((228, 0, 1308, 1920)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.eval(bg, lambda v: int(v * 0.55))
    bg.paste(b, (0, (1920 - 1350) // 2))
    ram = f"{tmp}/r{i}.png"; bg.save(ram)
    kl = f"{tmp}/k{i}.mp4"
    n = int(D * 30)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", ram, "-vf",
                    f"scale=1188:2112,zoompan=z='1+0.04*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps=30,format=yuv420p",
                    "-t", str(D), "-c:v", "libx264", "-preset", "medium", "-crf", "20", kl], check=True)
    klipp.append(kl)
# övertoningar
inp = sum([["-i", k] for k in klipp], [])
filt, prev, off = "", "[0:v]", D - F
for i in range(1, len(klipp)):
    lab = f"[v{i}]"
    filt += f"{prev}[{i}:v]xfade=transition=fade:duration={F}:offset={off:.2f}{lab};"
    prev, off = lab, off + D - F
filt = filt.rstrip(";")
# tyst ljudspår (Instagram vill ha ljudspår)
total = D * len(klipp) - F * (len(klipp) - 1)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inp, "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
                "-filter_complex", filt, "-map", prev, "-map", f"{len(klipp)}:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-crf", "21", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", ut], check=True)
print(ut, f"{total:.1f} s")
