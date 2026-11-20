"""Mini libreria geometrica per i loghi QdA: forme come tracciati booleani (skia-pathops),
testo convertito in tracciati (HarfBuzz + fontTools), export SVG pulito e PNG (cairosvg)."""
import math, os
import pathops
from pathops import Path, PathOp, LineCap, LineJoin
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import uharfbuzz as hb
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
K = 0.5522847498

# ---------- primitive ----------
def circle(cx, cy, r):
    p = Path()
    p.moveTo(cx + r, cy)
    p.cubicTo(cx + r, cy + K * r, cx + K * r, cy + r, cx, cy + r)
    p.cubicTo(cx - K * r, cy + r, cx - r, cy + K * r, cx - r, cy)
    p.cubicTo(cx - r, cy - K * r, cx - K * r, cy - r, cx, cy - r)
    p.cubicTo(cx + K * r, cy - r, cx + r, cy - K * r, cx + r, cy)
    p.close()
    return p

def rect(x, y, w, h):
    p = Path()
    p.moveTo(x, y); p.lineTo(x + w, y); p.lineTo(x + w, y + h); p.lineTo(x, y + h); p.close()
    return p

def rrect(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    k = K * r
    p = Path()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y); p.cubicTo(x + w - r + k, y, x + w, y + r - k, x + w, y + r)
    p.lineTo(x + w, y + h - r); p.cubicTo(x + w, y + h - r + k, x + w - r + k, y + h, x + w - r, y + h)
    p.lineTo(x + r, y + h); p.cubicTo(x + r - k, y + h, x, y + h - r + k, x, y + h - r)
    p.lineTo(x, y + r); p.cubicTo(x, y + r - k, x + r - k, y, x + r, y)
    p.close()
    return p

def polygon(pts):
    p = Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p

def arc_centerline(cx, cy, r, a0, a1, p=None, move=True):
    """Arco (gradi, y verso il basso, 0 = destra, 90 = basso) approssimato con cubiche <= 90°."""
    if p is None:
        p = Path()
    n = max(1, int(math.ceil(abs(a1 - a0) / 90.0)))
    da = (a1 - a0) / n
    t0 = math.radians(a0)
    if move:
        p.moveTo(cx + r * math.cos(t0), cy + r * math.sin(t0))
    for i in range(n):
        s = math.radians(a0 + i * da); e = math.radians(a0 + (i + 1) * da)
        h = 4 / 3 * math.tan((e - s) / 4) * r
        p.cubicTo(cx + r * math.cos(s) - h * math.sin(s), cy + r * math.sin(s) + h * math.cos(s),
                  cx + r * math.cos(e) + h * math.sin(e), cy + r * math.sin(e) - h * math.cos(e),
                  cx + r * math.cos(e), cy + r * math.sin(e))
    return p

def stroke(path, w, cap="butt", join="round"):
    q = Path(path)
    caps = {"butt": LineCap.BUTT_CAP, "round": LineCap.ROUND_CAP, "square": LineCap.SQUARE_CAP}
    joins = {"round": LineJoin.ROUND_JOIN, "miter": LineJoin.MITER_JOIN, "bevel": LineJoin.BEVEL_JOIN}
    q.stroke(w, caps[cap], joins[join], 4)
    q.convertConicsToQuads()
    return simplify(q)

def line(x0, y0, x1, y1):
    p = Path(); p.moveTo(x0, y0); p.lineTo(x1, y1)
    return p

def union(*ps):
    ps = [p for p in ps if p is not None]
    if not ps:
        return Path()
    out = Path(ps[0])
    for p in ps[1:]:
        out = pathops.op(out, p, PathOp.UNION)
    return out

def diff(a, *bs):
    out = Path(a)
    for b in bs:
        out = pathops.op(out, b, PathOp.DIFFERENCE)
    return out

def inter(a, b):
    return pathops.op(a, b, PathOp.INTERSECTION)

def simplify(p):
    return pathops.simplify(p, clockwise=False)

def transformed(p, a=1, b=0, c=0, d=1, e=0, f=0):
    return p.transform(a, b, c, d, e, f)

def tr(p, dx=0, dy=0, s=1):
    return p.transform(s, 0, 0, s, dx, dy)

def bounds(p):
    return p.bounds  # (xmin, ymin, xmax, ymax)

# ---------- testo -> tracciati ----------
_fonts = {}
def _font(file, loc):
    key = (file, tuple(sorted(loc.items())))
    if key not in _fonts:
        path = os.path.join(HERE, "fonts", file)
        tt = TTFont(path)
        gs = tt.getGlyphSet(location=loc) if loc else tt.getGlyphSet()
        blob = hb.Blob.from_file_path(path)
        face = hb.Face(blob)
        font = hb.Font(face)
        if loc:
            font.set_variations(loc)
        _fonts[key] = (tt, gs, font, tt["head"].unitsPerEm)
    return _fonts[key]

def text(s, size, file="Archivo[wdth,wght].ttf", loc=None, tracking=0, x=0, baseline=0, features=None):
    """Ritorna (Path, advance_width) con la linea di base a y=baseline, x iniziale = x.
    tracking in millesimi di em."""
    loc = loc or {}
    tt, gs, font, upm = _font(file, loc)
    buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
    hb.shape(font, buf, features or {"kern": True, "liga": True})
    sc = size / upm
    out = Path()
    pen_x = 0
    order = tt.getGlyphOrder()
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gname = order[info.codepoint]
        gp = Path()
        tp = TransformPen(gp.getPen(), (sc, 0, 0, -sc, x + (pen_x + pos.x_offset) * sc, baseline - pos.y_offset * sc))
        gs[gname].draw(tp)
        out = union(out, gp) if len(list(gp.contours)) else out
        pen_x += pos.x_advance + tracking * upm / 1000
    width = (pen_x - tracking * upm / 1000) * sc
    return simplify(out), width

# ---------- export ----------
def d(path, nd=1):
    pen = SVGPathPen(None, ntos=lambda v: (f"{round(v, nd):.{nd}f}").rstrip("0").rstrip(".") if nd else str(int(round(v))))
    path.draw(pen)
    return pen.getCommands()

def svg_doc(layers, vb, bg=None, title=None):
    """layers: lista di (Path, colore). vb: (x, y, w, h)."""
    x, y, w, h = [round(v, 1) for v in vb]
    def n(v):
        return f"{v:g}"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{n(x)} {n(y)} {n(w)} {n(h)}" width="{n(w)}" height="{n(h)}">']
    if title:
        parts.append(f"  <title>{title}</title>")
    if bg:
        parts.append(f'  <rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="{bg}"/>')
    # unisci i livelli con lo stesso colore
    merged = {}
    order = []
    for p, col in layers:
        if col not in merged:
            merged[col] = Path(); order.append(col)
        merged[col] = union(merged[col], p)
    for col in order:
        parts.append(f'  <path fill="{col}" d="{d(merged[col])}"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"

def save(svg, path_svg, png_widths=()):
    os.makedirs(os.path.dirname(path_svg), exist_ok=True)
    with open(path_svg, "w") as f:
        f.write(svg)
    outs = []
    for w, suffix in png_widths:
        out = path_svg[:-4] + suffix + ".png"
        cairosvg.svg2png(bytestring=svg.encode(), write_to=out, output_width=w)
        outs.append(out)
    return outs

def png(svg, out, w, h=None):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    kw = {"output_width": w}
    if h:
        kw["output_height"] = h
    cairosvg.svg2png(bytestring=svg.encode(), write_to=out, **kw)
    return out

# ---------- contrasto ----------
def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def lum(hexc):
    hexc = hexc.lstrip("#")
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)
