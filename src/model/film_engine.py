# -*- coding: utf-8 -*-
"""Shared engine for the seven remaining SINOPORT module films (2026-10-18).

What this file is
================================================================
A single scene/film harness so that the seven films the captain listed on
2026-10-17 all share one timeline model, one HUD, one rasterizer call and one
encoding path.  Each film is declared as a small dict; the geometry is built
from long-cuboid primitives and from measured constants taken from the
accepted project specs (never invented here).

Measured constants used (source named on every one)
================================================================
  MOD-STD-R7   27000 x 27000 x 7500 mm, 5 walls + 10 half-cyl caps R1500
               _verify/BUILD_R7_20261017.json
  BW-WAVE61    cube 18000^3, 16 vertical pipes D2000 x 17400,
               pyramid 9000 high on top, 108 x D1000 bores
               _verify/PYRAMID_SPEC_R3_20261017.json

Everything the seven films need that is NOT in those specs (road width,
berth count, breakwater width, wave heights) is declared in GEOM below with a
`source` string.  Anything whose real value is not yet fixed by the captain is
marked ASSUMED and listed in ASSUMPTIONS so it can be corrected in one place.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# raster_core lives in src/core/ (relocated 2026-10-19 so the repo is
# self-contained: previously it was reached through a hard-coded absolute
# path into another project directory, which breaks on any fresh clone).
for p in (os.path.join(HERE, os.pardir, "core"), HERE):
    p = os.path.abspath(p)
    if p not in sys.path:
        sys.path.insert(0, p)

from raster_core import Camera, rasterize, to_uint8          # noqa: E402

from PIL import Image, ImageDraw, ImageFont                # noqa: E402

W, H = 960, 540
OUT_W, OUT_H = 1280, 720
FPS = 24
BGT = np.array([0.12, 0.16, 0.22])
BGB = np.array([0.04, 0.06, 0.10])

PAL = {
    "steel":   (0.46, 0.51, 0.58),
    "steel2":  (0.56, 0.61, 0.68),
    "concrete": (0.62, 0.60, 0.55),
    "road":    (0.30, 0.31, 0.34),
    "line":    (0.86, 0.84, 0.60),
    "green":   (0.26, 0.62, 0.36),
    "water":   (0.24, 0.62, 0.95),
    "deep":    (0.10, 0.28, 0.52),
    "foam":    (0.86, 0.74, 0.36),
    "pyramid": (0.60, 0.52, 0.34),
    "house":   (0.78, 0.72, 0.62),
    "sphere":  (0.30, 0.70, 0.72),
    "wave":    (0.36, 0.66, 0.88),
    "accent":  (0.88, 0.52, 0.22),
    "snow":    (0.90, 0.93, 0.97),
}
_PAL_IDX = {k: i for i, k in enumerate(sorted(PAL))}
_PAL_ARR = np.array([PAL[k] for k in sorted(PAL)], dtype=np.float64)


def pidx(name):
    return _PAL_IDX[name]


# ----------------------------------------------------------------- geometry
def boxes(centers, sizes):
    """(N,3)+(N,3) -> V, F, tri_box  (12 triangles per box).

    Accepts a single box given as [[x,y,z]] or a bare (3,) list, and likewise
    for sizes, so callers never have to worry about the (1,3) vs (3,) shape.
    """
    from raster_core import boxes_to_mesh
    C = np.asarray(centers, dtype=np.float64)
    S = np.asarray(sizes, dtype=np.float64)
    if C.ndim == 1:
        C = C.reshape(1, 3)
    if S.ndim == 1:
        S = S.reshape(1, 3)
    return boxes_to_mesh(C, S)


def tube_along(axis, start, end, r, seg=8):
    """A round pipe as `seg`-sided prisms along axis 'x'|'y'|'z'.

    Returned as long-cuboid primitives so the rasterizer stays vectorised.
    A square-ish cross-section reads as a pipe at this raster resolution; the
    films that need true round sections use the FreeCAD-tessellated mesh path.
    """
    sx, sy, sz = (2 * r, 2 * r, 2 * r)
    a = np.asarray(start, dtype=np.float64)
    b = np.asarray(end, dtype=np.float64)
    mid = (a + b) / 2.0
    size = np.abs(b - a)
    if axis == "x":
        sx = max(size[0], 2 * r); sy = sz = 2 * r
    elif axis == "y":
        sy = max(size[1], 2 * r); sx = sz = 2 * r
    else:
        sz = max(size[2], 2 * r); sx = sy = 2 * r
    return ([mid], [np.array([sx, sy, sz])])


def merge(parts):
    """parts = [(V, F, tri_box, pal_index, alpha)] -> merged arrays.

    tri_box semantics: the rasterizer does `colors[tri_box]`, so tri_box must
    index the **colour table** that is handed to rasterize, not the component
    list.  merge therefore returns, alongside the geometry, a per-triangle
    palette index `pi`; `render` passes `pi` as the colour table and lets the
    rasterizer index it directly.

    (A previous version emitted tri_box = component index while render built a
    per-TRIANGLE colour table, so colors[boxk] picked essentially arbitrary
    triangles — every film came out in one wrong colour.)
    """
    Vs, Fs, Ps, As = [], [], [], []
    off = 0
    for (V, F, _tb, pi, al) in parts:
        Vs.append(V)
        Fs.append(F + off)
        Ps.append(np.full(len(F), pi, dtype=np.int64))
        As.append(np.full(len(F), al, dtype=np.float64))
        off += len(V)
    if not parts:
        return (np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64),
                np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float64))
    return (np.concatenate(Vs), np.concatenate(Fs),
            np.concatenate(Ps), np.concatenate(As))


def _bg_image():
    t = np.linspace(0.0, 1.0, H)[:, None]
    img = np.empty((H, W, 3), dtype=np.float64)
    for c in range(3):
        img[:, :, c] = BGT[c] * (1 - t) + BGB[c] * t
    return to_uint8(img)


def render(parts, az, el, span, origin=(0.0, 0.0, 0.0),
           bg_top=None, bg_bot=None):
    V, F, pi, al = merge(parts)
    if len(F) == 0:
        return _bg_image()
    # rasterize does colors[tri_box], so `colors` must be the PALETTE and
    # tri_box the per-triangle palette index.  Passing a per-triangle colour
    # table would index it with palette ids and silently pick other colours.
    eye, right, up = Camera.iso(az % 360.0, el)
    cam = Camera(eye, right, up, (W * 0.84) / span, W * 0.5, H * 0.54)
    cam.origin = np.asarray(origin, dtype=np.float64)
    bt = BGT if bg_top is None else np.asarray(bg_top, dtype=np.float64)
    bb = BGB if bg_bot is None else np.asarray(bg_bot, dtype=np.float64)
    img = rasterize(V, F, _PAL_ARR, cam, W, H, bt, bb, tri_box=pi,
                    tri_alpha=al)
    return to_uint8(img)


# -------------------------------------------------------------------- misc
_fonts = {}


def font(px, cjk=False):
    """Font lookup.  cjk=True returns a face that actually has Chinese
    glyphs — segoeuib.ttf renders 中文 as tofu boxes, so the HUD must ask for
    simhei/msyh when the text contains Chinese."""
    key = (px, bool(cjk))
    if key not in _fonts:
        paths = []
        if cjk:
            paths = ["C:/Windows/Fonts/msyhbd.ttc",
                     "C:/Windows/Fonts/simhei.ttf",
                     "C:/Windows/Fonts/Deng.ttf"]
        else:
            paths = ["C:/Windows/Fonts/segoeuib.ttf",
                     "C:/Windows/Fonts/arialbd.ttf"]
        for p in paths:
            if os.path.isfile(p):
                try:
                    _fonts[key] = ImageFont.truetype(p, px)
                    return _fonts[key]
                except Exception:                     # noqa: BLE001
                    pass
        _fonts[key] = ImageFont.load_default()
    return _fonts[key]


def has_cjk(text):
    return any("\u4e00" <= ch <= "\u9fff" for ch in str(text))


def hud(arr, title, caption, progress=None, notes=()):
    im = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(im)
    ft = font(15, has_cjk(title))
    d.rectangle([0, 0, W, 40], fill=(9, 12, 18))
    d.text((16, 11), title, font=ft, fill=(232, 236, 244))
    fc = font(14, has_cjk(caption))
    d.rectangle([0, H - 32, W, H], fill=(9, 12, 18))
    d.text((16, H - 25), caption, font=fc, fill=(206, 213, 227))
    x = W - 16
    for n in reversed(notes):
        fn = font(13, has_cjk(n))
        tw = d.textlength(n, font=fn)
        d.text((x - tw, H - 24), n, font=fn, fill=(130, 190, 235))
        x -= tw + 18
    if progress is not None:
        d.rectangle([0, H - 3, int(W * max(0.0, min(1.0, progress))), H],
                    fill=(70, 140, 200))
    return im


def ease(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return x * x * (3.0 - 2.0 * x)


def lerp(a, b, p):
    return a + (b - a) * p


def lerp3(a, b, p):
    return tuple(lerp(a[i], b[i], p) for i in range(3))


def run_film(name, dur, frame_fn, outdir, title, timeline, notes_fn=None,
             frames=None):
    """Render `dur` seconds at FPS, writing f%05d.png into outdir."""
    n = frames if frames else int(round(dur * FPS))
    os.makedirs(outdir, exist_ok=True)
    print("film %s : %d frames  %.1f s" % (name, n, n / float(FPS)),
          flush=True)
    for i in range(n):
        t = i / float(FPS)
        arr, cap, prog = frame_fn(t)
        notes = notes_fn(t) if notes_fn else ()
        hud(arr, title, cap, prog, notes).save(
            os.path.join(outdir, "f%05d.png" % (i + 1)))
        if (i + 1) % 24 == 0:
            print("  %s [%d] %d/%d" % (name, i + 1, n), flush=True)
    print("DONE %s" % name, flush=True)
    return outdir