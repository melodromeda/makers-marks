"""
prepare_layers.py - publish a TouchDesigner image sequence as a "layers" painting.

  python tools/prepare_layers.py path/to/exported/frames --title "Night one" --push

Keeps ~80 evenly spaced frames, shrinks them to 1024 px, writes them into
paintings/<date_time>/ with a manifest and thumbnail, adds it to the gallery list,
and (with --push) uploads to GitHub.   Needs: pip install pillow

Also:  python tools/prepare_layers.py --qr https://you.github.io/makers-marks/
       writes qr.png for printing (needs: pip install qrcode)
"""
import argparse, datetime, json, os, re, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("src", nargs="?")
ap.add_argument("--title", default="")
ap.add_argument("--max", type=int, default=80)
ap.add_argument("--size", type=int, default=1024)
ap.add_argument("--depth", type=float, default=1.2)
ap.add_argument("--key", default="luminance", choices=["luminance", "alpha", "none"])
ap.add_argument("--blending", default="additive", choices=["additive", "normal"])
ap.add_argument("--opacity", type=float, default=0.35)
ap.add_argument("--reverse", action="store_true")
ap.add_argument("--push", action="store_true")
ap.add_argument("--qr")
a = ap.parse_args()

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if a.qr:
    import qrcode
    qrcode.make(a.qr, box_size=20, border=2).save(os.path.join(repo, "qr.png"))
    print("wrote qr.png ->", a.qr)
if not a.src:
    sys.exit(0 if a.qr else "give the folder of exported frames")

natural = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]
files = sorted([f for f in os.listdir(a.src) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"))], key=natural)
if not files:
    sys.exit("no images in " + a.src)
if len(files) > a.max:
    step = (len(files) - 1) / (a.max - 1)
    files = [files[round(i * step)] for i in range(a.max)]

from PIL import Image
now = datetime.datetime.now()
pid = now.strftime("%Y-%m-%d_%H%M%S")
out = os.path.join(repo, "paintings", pid)
os.makedirs(out)
names = []
for i, f in enumerate(files):
    im = Image.open(os.path.join(a.src, f)).convert("RGBA" if a.key == "alpha" else "RGB")
    im.thumbnail((a.size, a.size), Image.LANCZOS)
    name = f"layer_{i:04d}." + ("png" if a.key == "alpha" else "jpg")
    im.save(os.path.join(out, name), **({"optimize": True} if a.key == "alpha" else {"quality": 88}))
    names.append(name)
    if i == len(files) // 2:
        t = im.convert("RGB"); t.thumbnail((600, 600)); t.save(os.path.join(out, "thumb.jpg"), quality=85)
    print(f"\r{i + 1}/{len(files)}", end="")
print()
json.dump(dict(files=names, depth=a.depth, key=a.key, blending=a.blending, opacity=a.opacity, reverse=a.reverse),
          open(os.path.join(out, "manifest.json"), "w"), indent=2)

idx_path = os.path.join(repo, "paintings", "index.json")
idx = json.load(open(idx_path)) if os.path.exists(idx_path) else []
idx.append({"id": pid, "kind": "layers", "date": now.isoformat(timespec="seconds"), "title": a.title, "thumb": "thumb.jpg"})
json.dump(idx, open(idx_path, "w"), indent=1)
print("saved painting", pid)

if a.push:
    g = lambda *x: subprocess.run(["git", "-C", repo, *x])
    g("add", "paintings"); g("commit", "-m", "add painting " + pid); g("pull", "--rebase", "--autostash"); g("push")
