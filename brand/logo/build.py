"""Build finale: 3 concetti -> cartelle concetto-X con tutte le versioni."""
import math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qda import *

DEST = sys.argv[1] if len(sys.argv) > 1 else "/home/user/anthropic-claude-code/brand/logo"
INK, WHITE = "#14161A", "#FFFFFF"
FONT_LOC = {"wght": 800, "wdth": 108}

def pol(cx, cy, r, a):
    t = math.radians(a)
    return cx + r * math.cos(t), cy + r * math.sin(t)

def recenter(layers):
    x0, y0, x1, y1 = union(*[p for p, _ in layers]).bounds
    dx, dy = -(x0 + x1) / 2, -(y0 + y1) / 2
    return [(tr(p, dx, dy), r) for p, r in layers]

# ------------------------------------------------------------------ simboli
# ogni simbolo restituisce [(Path, ruolo)], ruolo = "a" (colore principale) | "b" (secondo elemento)

# ------------------------------------------------------------------ concetti
LOC = {"wght": 800, "wdth": 100}

def sym_qxa(xs_ratio=0.62, w_ratio=0.86, sb=0.13):
    """Q×A. La × ha lo spessore delle aste (corretto otticamente: le diagonali appaiono più pesanti)."""
    size = 600
    Q, wq = text("Q", size, loc=LOC); A, wa = text("A", size, loc=LOC)
    stem = 107.7; cap = 412.3
    xs = cap * xs_ratio                         # lato del quadrato della ×
    sw = stem * w_ratio
    xc_y = -cap / 2
    qb, ab = Q.bounds, A.bounds
    space = size * sb                           # spazio bianco uguale ai due lati della ×
    x0 = qb[2] + space
    h = xs / 2
    X = union(stroke(line(x0, xc_y - h, x0 + xs, xc_y + h), sw, "butt"),
              stroke(line(x0, xc_y + h, x0 + xs, xc_y - h), sw, "butt"))
    X = inter(X, rect(x0, xc_y - h, xs, xs))    # taglia le punte a filo del quadrato
    Ap = tr(A, x0 + xs + space - ab[0], 0)
    return recenter([(union(Q, Ap), "b"), (X, "a")])

def sym_traccia(t=84, r=220, stem_len=140):
    """Il ? è la traccia del movimento (bar path) della video-analisi."""
    p = arc_centerline(0, 0, r, 180, 450); p.lineTo(0, r + stem_len)
    solid = stroke(p, t, "round")
    trail = Path()
    for i, (a, k) in enumerate([(157, 0.40), (139, 0.31), (124, 0.23)]):
        trail = union(trail, circle(*pol(0, 0, r, a), t * k))
    mr = t * 1.05
    my = r + stem_len + t / 2 + 46 + mr
    marker = union(diff(circle(0, my, mr), circle(0, my, mr - t * 0.42)), circle(0, my, t * 0.36))
    return recenter([(union(solid, trail), "b"), (marker, "a")])

def sym_ib(t=104, r=190, gap=22):
    """?! (interrobang): l'arco del ? in un colore, l'asta e il punto del ! nell'altro."""
    arc = stroke(arc_centerline(0, 0, r, 180, 450), t, "round")
    stem_h = r * 2 + 150
    stem = rrect(-t / 2, -r - t / 2, t, stem_h, t / 2)
    dot = circle(0, -r - t / 2 + stem_h + 50 + t * 0.6, t * 0.6)
    halo = rrect(-t / 2 - gap, -r - t / 2 - gap, t + 2 * gap, stem_h + 2 * gap, t / 2 + gap)
    return recenter([(diff(arc, halo), "a"), (union(stem, dot), "b")])

CONCEPTS = {
    1: dict(slug="concetto-1", name="Q×A", sym=sym_qxa,
            idea="La 'd' di QdA diventa la × della scheda di allenamento (3×10): il nome si scrive come una serie. "
                 "E si legge anche Q&A, domande e risposte: quello che fa il profilo.",
            palette=[("Blu cobalto", "#1F33D6"), ("Lime", "#D7FF3A"), ("Nero inchiostro", INK), ("Bianco", WHITE)],
            light={"a": "#1F33D6", "b": INK, "text": INK},
            dark={"a": "#D7FF3A", "b": WHITE, "text": WHITE, "bg": INK},
            brand={"a": "#D7FF3A", "b": WHITE, "text": WHITE, "bg": "#1F33D6"},
            profile="brand"),
    2: dict(slug="concetto-2", name="La traccia", sym=sym_traccia,
            idea="Il punto interrogativo è la traccia del movimento che si vede nella video-analisi degli esercizi: "
                 "scia di punti, curva e marker di tracciamento al posto del punto.",
            palette=[("Arancio segnale", "#FF5A1F"), ("Arancio bruciato", "#C93A0C"), ("Nero inchiostro", INK), ("Bianco", WHITE)],
            light={"a": "#C93A0C", "b": INK, "text": INK},
            dark={"a": "#FF5A1F", "b": WHITE, "text": WHITE, "bg": INK},
            brand={"a": "#FF5A1F", "b": WHITE, "text": WHITE, "bg": INK},
            profile="brand"),
    3: dict(slug="concetto-3", name="?!", sym=sym_ib,
            idea="Domanda e risposta in un solo segno (interrobang): il ? è il dubbio con cui arrivi in sala, "
                 "il ! è la risposta del trainer. Serio nella costruzione, ironico nel tono.",
            palette=[("Giallo", "#FFC400"), ("Viola", "#5B3FE0"), ("Nero inchiostro", INK), ("Bianco", WHITE)],
            light={"a": "#5B3FE0", "b": INK, "text": INK},
            dark={"a": "#FFC400", "b": WHITE, "text": WHITE, "bg": INK},
            brand={"a": "#FFC400", "b": WHITE, "text": WHITE, "bg": INK},
            profile="brand"),
}

# ------------------------------------------------------------------ wordmark
def wordmark(size=100):
    """Due righe giustificate alla stessa larghezza: QUESTIONE DI / ALLENAMENTO."""
    l2, w2 = text("ALLENAMENTO", size, loc=FONT_LOC, tracking=40)
    # trova il tracking della riga 1 che la porta alla stessa larghezza della riga 2
    lo, hi = -50, 400
    for _ in range(30):
        mid = (lo + hi) / 2
        _, w1 = text("QUESTIONE DI", size, loc=FONT_LOC, tracking=mid)
        lo, hi = (mid, hi) if w1 < w2 else (lo, mid)
    l1, w1 = text("QUESTIONE DI", size, loc=FONT_LOC, tracking=lo)
    lead = size * 1.0
    l2 = tr(l2, 0, lead)
    # allinea i bordi reali (bordo sinistro ottico)
    b1, b2 = l1.bounds, l2.bounds
    l1 = tr(l1, -b1[0], 0); l2 = tr(l2, -b2[0], 0)
    wm = union(l1, l2)
    x0, y0, x1, y1 = wm.bounds
    return tr(wm, -x0, -y0)  # origine in alto a sinistra

def place(layers, scale, dx, dy):
    return [(p.transform(scale, 0, 0, scale, dx, dy), r) for p, r in layers]

def lockup_h(sym):
    wm = wordmark()
    wx0, wy0, wx1, wy1 = wm.bounds
    th = wy1 - wy0
    sx0, sy0, sx1, sy1 = union(*[p for p, _ in sym]).bounds
    target_h = th * 1.32                              # il simbolo eccede un po' il blocco di testo (compensazione ottica)
    s = target_h / (sy1 - sy0)
    symp = place(sym, s, -sx0 * s, -sy0 * s)
    gap = th * 0.42
    sw = (sx1 - sx0) * s
    txt = tr(wm, sw + gap, (target_h - th) / 2)
    return symp + [(txt, "text")]

def lockup_v(sym):
    wm = wordmark()
    wx0, wy0, wx1, wy1 = wm.bounds
    tw, th = wx1 - wx0, wy1 - wy0
    sx0, sy0, sx1, sy1 = union(*[p for p, _ in sym]).bounds
    s = (th * 2.5) / (sy1 - sy0)
    sw, sh = (sx1 - sx0) * s, (sy1 - sy0) * s
    W = max(tw, sw)
    symp = place(sym, s, (W - sw) / 2 - sx0 * s, -sy0 * s)
    gap = th * 0.45
    txt = tr(wm, (W - tw) / 2, sh + gap)
    return symp + [(txt, "text")]

def colorize(layers, scheme):
    return [(p, scheme[r]) for p, r in layers]

def vb_of(layers, pad_ratio=0.06):
    x0, y0, x1, y1 = union(*[p for p, _ in layers]).bounds
    pad = max(x1 - x0, y1 - y0) * pad_ratio
    return (x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad)

def norm(layers, pad_ratio=0.06):
    """Porta il contenuto in coordinate positive con origine 0,0 e restituisce (layers, viewBox)."""
    x, y, w, h = vb_of(layers, pad_ratio)
    return [(tr(p, -x, -y), c) for p, c in layers], (0, 0, w, h)

def max_radius(path, cx, cy, steps=24):
    """Distanza massima dal centro misurata campionando le curve (stima conservativa)."""
    m = 0
    for contour in path.contours:
        for verb, pts in contour.segments:
            for p in pts:
                if p is None:
                    continue
                m = max(m, math.hypot(p[0] - cx, p[1] - cy))
    return m

def profile(sym, scheme, size=1080, margin=0.15):
    """Simbolo dentro il cerchio di sicurezza: raggio utile = (0.5 - margin) * size."""
    allp = union(*[p for p, _ in sym])
    x0, y0, x1, y1 = allp.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rmax = max_radius(allp, cx, cy)
    safe = (0.5 - margin) * size
    s = safe / rmax
    L = place(sym, s, size / 2 - cx * s, size / 2 - cy * s)
    return colorize(L, scheme), s * rmax

# ------------------------------------------------------------------ mockup post 1080x1350
def mockup(sym, c):
    sch = c[c["profile"]]
    bg = sch["bg"]
    W, H = 1080, 1350
    layers = []
    # simbolo grande, ancorato in alto a sinistra sulla griglia di 90 px
    sl = place(sym, 1, 0, 0)
    x0, y0, x1, y1 = union(*[p for p, _ in sl]).bounds
    s = 300 / (y1 - y0)
    layers += colorize(place(sym, s, 90 - x0 * s, 90 - y0 * s), sch)
    # titolo del post
    lines = ["IL PROBLEMA", "NON È IL PESO.", "È COME LO", "SOLLEVI."]
    y = 640
    for i, ln in enumerate(lines):
        p, w = text(ln, 104, loc={"wght": 800, "wdth": 100}, tracking=0, x=90, baseline=y + i * 112)
        layers.append((p, sch["a"] if i >= 2 else sch["text"]))
    # firma in basso: wordmark piccolo + filetto
    wm = wordmark(40)
    wx0, wy0, wx1, wy1 = wm.bounds
    layers.append((tr(wm, 90, H - 90 - (wy1 - wy0)), sch["text"]))
    sw, w2 = text("SCORRI →", 30, loc={"wght": 600, "wdth": 100}, tracking=80)
    bx = sw.bounds
    layers.append((tr(sw, W - 90 - bx[2], H - 90), sch["text"]))
    layers.append((rect(90, H - 90 - (wy1 - wy0) - 46, W - 180, 4), sch["text"]))
    return svg_doc(layers, (0, 0, W, H), bg=bg, title="Mockup post 1080x1350")

# ------------------------------------------------------------------ build
def build(n):
    c = CONCEPTS[n]
    out = os.path.join(DEST, c["slug"])
    os.makedirs(out, exist_ok=True)
    sym = c["sym"]()
    report = {"name": c["name"]}
    files = {}

    def emit(name, layers, title, bg=None, pad=0.06, pngw=2000):
        L, vb = norm(layers, pad)
        svg = svg_doc(L, vb, bg=bg, title=title)
        p = os.path.join(out, name + ".svg")
        with open(p, "w") as f:
            f.write(svg)
        if pngw:
            png(svg, os.path.join(out, name + ".png"), pngw)
        files[name] = vb
        return svg

    light = c["light"]
    title = f"Questione di Allenamento — {c['name']}"
    emit("logo-orizzontale", colorize(lockup_h(sym), light), title)
    emit("logo-verticale", colorize(lockup_v(sym), light), title)
    emit("simbolo", colorize(sym, light), title, pad=0.08)
    mono_k = {"a": INK, "b": INK, "text": INK}
    mono_w = {"a": WHITE, "b": WHITE, "text": WHITE}
    emit("mono-nero", colorize(lockup_h(sym), mono_k), title + " (mono nero)")
    emit("mono-bianco", colorize(lockup_h(sym), mono_w), title + " (mono bianco)")
    # varianti extra: negativo su sfondo scuro e simbolo mono
    d = c["dark"]
    emit("logo-orizzontale-negativo", colorize(lockup_h(sym), d), title + " (negativo)", bg=d["bg"], pngw=2000)
    emit("simbolo-mono-nero", colorize(sym, mono_k), title, pad=0.08)
    emit("simbolo-mono-bianco", colorize(sym, mono_w), title, pad=0.08)
    # foto profilo
    sch = c[c["profile"]]
    pl, r_used = profile(sym, sch)
    svg = svg_doc(pl, (0, 0, 1080, 1080), bg=sch["bg"], title=title + " (foto profilo)")
    with open(os.path.join(out, "foto-profilo.svg"), "w") as f:
        f.write(svg)
    png(svg, os.path.join(out, "foto-profilo-1080.png"), 1080)
    png(svg, os.path.join(out, "foto-profilo-110.png"), 110)
    report["profile_radius"] = round(r_used, 1)
    # mockup
    msvg = mockup(sym, c)
    with open(os.path.join(out, "mockup-post.svg"), "w") as f:
        f.write(msvg)
    png(msvg, os.path.join(out, "mockup-post-1080x1350.png"), 1080)
    # anteprime 1080/110 del simbolo per il controllo
    s_svg = open(os.path.join(out, "simbolo.svg")).read()
    report["files"] = sorted(os.listdir(out))
    return report

if __name__ == "__main__":
    rep = {n: build(n) for n in CONCEPTS}
    meta = {n: {k: v for k, v in CONCEPTS[n].items() if k != "sym"} for n in CONCEPTS}
    with open(os.path.join(DEST, "concetti.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(rep, indent=1, ensure_ascii=False))
