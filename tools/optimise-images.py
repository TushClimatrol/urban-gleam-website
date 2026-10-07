#!/usr/bin/env python3
"""Urban Gleam image optimiser.

Run from the repo root whenever a photo is added or swapped:  python3 tools/optimise-images.py
(needs Pillow:  pip install Pillow)

For every photo listed in tools/photos.json it
  * records the JPEG's real width/height (so pages can reserve space and avoid layout shift), and
  * writes smaller WebP copies next to it (up to 1280px wide, plus a 640px one for phones).
The original JPEG stays as the fallback that Google Images indexes. Safe to run again: existing
WebP files are only rebuilt when the JPEG is newer.
"""
import json, os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
MANIFEST = 'tools/photos.json'
SMALL, LARGE = 640, 1280
QUALITY = 78

m = json.load(open(MANIFEST, encoding='utf-8'))
for p in m['gallery']:
    src = os.path.join('img', p['file'])
    if not os.path.exists(src):
        sys.exit(f'missing image: {src}')
    im = Image.open(src).convert('RGB')
    w, h = im.size
    p['w'], p['h'] = w, h
    big = min(w, LARGE)
    targets = [SMALL, big] if big >= SMALL * 1.3 else [big]
    variants = []
    for tw in targets:
        th = round(h * tw / w)
        out = os.path.join('img', f"{os.path.splitext(p['file'])[0]}-{tw}.webp")
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
            (im if tw == w else im.resize((tw, th), Image.LANCZOS)).save(out, 'WEBP', quality=QUALITY, method=6)
        variants.append({'file': os.path.basename(out), 'w': tw})
    p['webp'] = variants
    print(f"{p['file']:62} {w}x{h}  ->  " + ', '.join(f"{v['w']}w {os.path.getsize(os.path.join('img', v['file'])) // 1024}KB" for v in variants))

json.dump(m, open(MANIFEST, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print('manifest updated:', MANIFEST)
