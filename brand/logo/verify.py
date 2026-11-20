import os, sys, json, math, glob, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from fontTools.svgLib.path import parse_path
import pathops
from PIL import Image
from qda import contrast
D = sys.argv[1]
meta = json.load(open(os.path.join(D, "concetti.json")))
res = {}
for n, c in meta.items():
    folder = os.path.join(D, c["slug"]); r = {}
    svgs = sorted(glob.glob(folder + "/*.svg"))
    font_ok = clip_ok = valid_ok = True; notes = []
    for f in svgs:
        raw = open(f).read()
        try:
            root = etree.fromstring(raw.encode())
        except Exception as e:
            valid_ok = False; notes.append(f"{f}: {e}"); continue
        ns = "{http://www.w3.org/2000/svg}"
        if root.tag != ns + "svg" or not root.get("viewBox"): valid_ok = False
        if re.search(r"<text|<tspan|font-family|@font-face|<use|transform=", raw): font_ok = False; notes.append(f)
        x, y, w, h = map(float, root.get("viewBox").split())
        for p in root.iter(ns + "path"):
            P = pathops.Path(); parse_path(p.get("d"), P.getPen())
            bx0, by0, bx1, by1 = P.bounds
            if bx0 < x - 0.05 or by0 < y - 0.05 or bx1 > x + w + 0.05 or by1 > y + h + 0.05:
                clip_ok = False; notes.append(f"clip {os.path.basename(f)}")
    # PNG trasparenti 2000 px: bordo vuoto
    for name in ["logo-orizzontale", "logo-verticale", "simbolo", "mono-nero", "mono-bianco"]:
        im = Image.open(f"{folder}/{name}.png").convert("RGBA")
        a = im.getchannel("A"); W, H = im.size
        edge = max(max(a.crop((0, 0, W, 2)).getdata()), max(a.crop((0, H - 2, W, H)).getdata()),
                   max(a.crop((0, 0, 2, H)).getdata()), max(a.crop((W - 2, 0, W, H)).getdata()))
        if W != 2000 or edge != 0 or a.getextrema()[0] != 0: clip_ok = False; notes.append(f"png {name} {W} edge={edge}")
    # foto profilo: tutto il disegno dentro il raggio 0.35*1080
    im = Image.open(f"{folder}/foto-profilo-1080.png").convert("RGB"); bg = im.getpixel((0, 0))
    px = im.load(); maxr = 0
    for yy in range(0, 1080, 2):
        for xx in range(0, 1080, 2):
            if px[xx, yy] != bg: maxr = max(maxr, math.hypot(xx - 540, yy - 540))
    r["margine_profilo_%"] = round((540 - maxr) / 1080 * 100, 1)
    # mono: un solo colore
    mono = all(len(set(re.findall(r'fill="(#[0-9A-Fa-f]{6})"', open(f"{folder}/{m}.svg").read()))) == 1 for m in ["mono-nero", "mono-bianco", "simbolo-mono-nero", "simbolo-mono-bianco"])
    # contrasti delle coppie effettivamente usate
    pairs = []
    for sch, bgc in [("light", "#FFFFFF"), ("dark", c["dark"]["bg"]), ("brand", c["brand"]["bg"])]:
        for role in ("a", "b", "text"):
            pairs.append((sch, role, c[sch][role], bgc, round(contrast(c[sch][role], bgc), 2)))
    r.update(svg=len(svgs), font_in_tracciati=font_ok, nessun_taglio=clip_ok, svg_validi=valid_ok, mono_un_colore=mono,
             contrasto_min=min(p[4] for p in pairs), coppie=pairs, note=notes)
    res[n] = r
print(json.dumps(res, indent=1, ensure_ascii=False))
