"""Build every OpenMedGate brand asset from one definition of the mark.

    python asset-sources/brand/build_brand.py [--shared <folder>]

Writes to static/brand/ (SVG and PNG), static/favicon.svg, static/apple-touch-icon.png and
static/images/og/openmedgate-og.png. With --shared, copies the brand set into that folder as well.

The mark ("Puls przez brame"): two square brackets, each cut where an ECG trace passes through.
The wordmark is Manrope 800 converted to outlines; glyph positions are measured in Chromium so the
outlines carry the same kerning as the rendered text.
"""
from __future__ import annotations

import argparse
import base64
import shutil
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "static" / "brand"
FONT = ROOT / "static" / "fonts" / "manrope-normal-200-800-latin.woff2"
POSTER = ROOT / "static" / "media" / "hero" / "open-flow-poster.jpg"

NIGHT, WHITE, MINT, MINT_DEEP = "#06111b", "#f3f7fa", "#17e39a", "#0a8a5e"

# Colour variants: (key, bracket colour, pulse colour, wordmark colour, "Open" colour)
VARIANTS = {
    "k1-mieta-bialy": (WHITE, MINT, WHITE, MINT),        # on dark backgrounds
    "k2-mieta-noc": (NIGHT, MINT_DEEP, NIGHT, MINT_DEEP),  # on light backgrounds
    "k3-bialy": (WHITE, WHITE, WHITE, WHITE),
    "k4-noc": (NIGHT, NIGHT, NIGHT, NIGHT),
    "k5-mieta": (MINT, MINT, MINT, MINT),
}

MARK_BRACKETS = "M23 11H11v13M11 40v13h12M41 11h12v13M53 40v13H41"
MARK_PULSE = "M2 32h20l5-12 6 24 5-12h24"


def mark_group(bracket: str, pulse: str, scale: float = 1.0, dx: float = 0, dy: float = 0) -> str:
    return (f'<g transform="translate({dx} {dy}) scale({scale})">'
            f'<path d="{MARK_BRACKETS}" fill="none" stroke="{bracket}" stroke-width="6" stroke-linecap="square" stroke-linejoin="miter"/>'
            f'<path d="{MARK_PULSE}" fill="none" stroke="{pulse}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g>')


def svg(width, height, body, viewbox=None):
    vb = viewbox or f"0 0 {width} {height}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{vb}">{body}</svg>')


# ---------------------------------------------------------------- wordmark outlines

class Wordmark:
    """Outlines of "OpenMedGate" in Manrope 800, kerned as Chromium renders it."""

    def __init__(self, page):
        font = TTFont(FONT)
        if "fvar" in font:
            font = instancer.instantiateVariableFont(font, {"wght": 800})
        self.font = font
        self.upem = font["head"].unitsPerEm
        self.cap = font["OS/2"].sCapHeight or int(self.upem * 0.72)
        self.text = "OpenMedGate"
        b64 = base64.b64encode(FONT.read_bytes()).decode()
        size = 400
        page.set_content(f"""<!doctype html><html><head><meta charset="utf-8"><style>
            @font-face{{font-family:M;font-weight:200 800;src:url(data:font/woff2;base64,{b64}) format("woff2")}}
            body{{margin:0}} #w{{font:800 {size}px M;letter-spacing:-0.035em;white-space:nowrap;display:inline-block}}
            </style></head><body><span id="w">{self.text}</span></body></html>""")
        page.wait_for_function("document.fonts.check('800 400px M')")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)
        lefts = page.evaluate("""() => { const el = document.getElementById('w'); const t = el.firstChild; const base = el.getBoundingClientRect().left;
            const out = []; for (let i = 0; i < t.length; i++) { const r = document.createRange(); r.setStart(t, i); r.setEnd(t, i + 1);
            out.push(r.getBoundingClientRect().left - base); } return out; }""")
        self.offsets = [x / size * self.upem for x in lefts]  # font units
        gs = font.getGlyphSet()
        cmap = font.getBestCmap()
        self.glyphs = []
        for ch, x in zip(self.text, self.offsets):
            name = cmap[ord(ch)]
            self.glyphs.append((ch, name, x, gs[name].width))
        last = self.glyphs[-1]
        self.width_units = last[2] + last[3]

    def paths(self, scale: float, x0: float, baseline: float, colour_open: str, colour_rest: str) -> str:
        """SVG paths for the wordmark with cap height = scale * cap units, baseline at y=baseline."""
        gs = self.font.getGlyphSet()
        parts = []
        for i, (ch, name, x, adv) in enumerate(self.glyphs):
            pen = SVGPathPen(gs)
            tpen = TransformPen(pen, (scale, 0, 0, -scale, x0 + x * scale, baseline))
            gs[name].draw(tpen)
            colour = colour_open if i < 4 else colour_rest
            parts.append(f'<path d="{pen.getCommands()}" fill="{colour}"/>')
        return "".join(parts)

    def width(self, scale: float) -> float:
        return self.width_units * scale


# ---------------------------------------------------------------- compositions

def lockup_horizontal(wm: Wordmark, bracket, pulse, text, open_colour) -> tuple[str, float, float]:
    cap_units = 34.0                      # cap height in mark units (mark is 64 tall, brackets 42)
    scale = cap_units / wm.cap
    gap = 16.0
    x_text = 64 + gap
    baseline = 32 + cap_units / 2
    w = x_text + wm.width(scale) + 4
    body = mark_group(bracket, pulse) + wm.paths(scale, x_text, baseline, open_colour, text)
    return svg(round(w * 10), 640, body, f"0 0 {w:.2f} 64"), w, 64


def lockup_stacked(wm: Wordmark, bracket, pulse, text, open_colour) -> tuple[str, float, float]:
    cap_units = 22.0
    scale = cap_units / wm.cap
    tw = wm.width(scale)
    w = max(tw, 64) + 16
    mark_scale = 1.15
    mx = (w - 64 * mark_scale) / 2
    baseline = 64 * mark_scale + 10 + cap_units
    h = baseline + 10
    body = mark_group(bracket, pulse, mark_scale, mx, 0) + wm.paths(scale, (w - tw) / 2, baseline, open_colour, text)
    return svg(round(w * 10), round(h * 10), body, f"0 0 {w:.2f} {h:.2f}"), w, h


def tile(bg: str, bracket: str, pulse: str, radius: float, mark_scale: float = 0.62) -> str:
    s = 64 * mark_scale
    off = (64 - s) / 2
    body = f'<rect width="64" height="64" rx="{radius}" fill="{bg}"/>' + mark_group(bracket, pulse, mark_scale, off, off)
    return svg(1024, 1024, body, "0 0 64 64")


def circle_tile(bg: str, bracket: str, pulse: str, mark_scale: float = 0.6) -> str:
    s = 64 * mark_scale
    off = (64 - s) / 2
    body = f'<circle cx="32" cy="32" r="32" fill="{bg}"/>' + mark_group(bracket, pulse, mark_scale, off, off)
    return svg(1024, 1024, body, "0 0 64 64")


# ---------------------------------------------------------------- rendering

def render_svg_png(page, svg_text: str, out_png: Path, width: int, height: int, transparent: bool = True):
    page.set_viewport_size({"width": width, "height": height})
    bg = "transparent" if transparent else "#ffffff"
    page.set_content(f'<!doctype html><html><body style="margin:0;background:{bg}">'
                     f'<div style="width:{width}px;height:{height}px;display:grid;place-items:center">'
                     f'{svg_text.replace(chr(10), "")}</div></body></html>')
    page.evaluate("""([w,h]) => { const s = document.querySelector('svg'); s.setAttribute('width', w); s.setAttribute('height', h); }""", [width, height])
    page.wait_for_timeout(80)
    page.screenshot(path=str(out_png), omit_background=transparent, clip={"x": 0, "y": 0, "width": width, "height": height})


def render_html_png(page, html: str, out_png: Path, width: int, height: int):
    page.set_viewport_size({"width": width, "height": height})
    page.set_content(html)
    page.wait_for_timeout(400)
    page.screenshot(path=str(out_png), clip={"x": 0, "y": 0, "width": width, "height": height})


def banner_html(lockup_svg: str, title: str, line: str, poster_b64: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
    body{{margin:0;width:1584px;height:396px;background:{NIGHT};position:relative;overflow:hidden;font-family:system-ui}}
    .bg{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{poster_b64}) center/cover;opacity:.9}}
    .shade{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(6,17,27,.92) 0%,rgba(6,17,27,.75) 45%,rgba(6,17,27,.15) 100%)}}
    .wrap{{position:absolute;left:96px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:26px}}
    .lock svg{{height:84px;width:auto;display:block}}
    .t{{color:rgba(243,247,250,.85);font-size:28px;letter-spacing:.01em}}
    .u{{color:{MINT};font-size:16px;letter-spacing:.14em;text-transform:uppercase;font-family:ui-monospace,Consolas,monospace}}
    </style></head><body><div class="bg"></div><div class="shade"></div>
    <div class="wrap"><div class="lock">{lockup_svg}</div><div class="t">{title}</div><div class="u">{line}</div></div></body></html>"""


def social_html(lockup_svg: str, poster_b64: str, size: int) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
    body{{margin:0;width:{size}px;height:{size}px;background:{NIGHT};position:relative;overflow:hidden}}
    .bg{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{poster_b64}) center/cover;opacity:.85}}
    .shade{{position:absolute;inset:0;background:radial-gradient(70% 70% at 50% 50%,rgba(6,17,27,.2),rgba(6,17,27,.9))}}
    .wrap{{position:absolute;inset:0;display:grid;place-items:center}} .wrap svg{{width:{int(size*0.52)}px;height:auto}}
    </style></head><body><div class="bg"></div><div class="shade"></div><div class="wrap">{lockup_svg}</div></body></html>"""


def og_html(lockup_svg: str, poster_b64: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
    body{{margin:0;width:1200px;height:630px;background:{NIGHT};position:relative;overflow:hidden;font-family:system-ui}}
    .bg{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{poster_b64}) center/cover;opacity:.9}}
    .shade{{position:absolute;inset:0;background:radial-gradient(70% 90% at 18% 75%,rgba(6,17,27,.85),transparent 65%),linear-gradient(180deg,rgba(6,17,27,.3),rgba(6,17,27,.85))}}
    .wrap{{position:absolute;inset:60px 72px;display:flex;flex-direction:column;justify-content:space-between}}
    .lock svg{{height:64px;width:auto;display:block}}
    h1{{margin:0;color:{WHITE};font-weight:800;font-size:76px;line-height:.98;letter-spacing:-.04em;max-width:14ch;font-family:M,system-ui}}
    .foot{{display:flex;justify-content:space-between;font-family:ui-monospace,Consolas,monospace;font-size:15px;letter-spacing:.1em;text-transform:uppercase;color:rgba(243,247,250,.7)}}
    </style></head><body><div class="bg"></div><div class="shade"></div>
    <div class="wrap"><div class="lock">{lockup_svg}</div><h1>Health data must be able to move.</h1>
    <div class="foot"><span>openmedgate.com</span><span>A movement for open interfaces in healthcare</span></div></div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shared", help="folder to receive a copy of the brand set (e.g. the Shared repository)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    poster_b64 = base64.b64encode(POSTER.read_bytes()).decode()
    font_b64 = base64.b64encode(FONT.read_bytes()).decode()
    written = []

    def put(name: str, text: str):
        p = OUT / name
        p.write_text(text, encoding="utf-8")
        written.append(p)
        return p

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1200, "height": 600}, device_scale_factor=1)
        wm = Wordmark(page)
        print("wordmark measured:", [round(x) for x in wm.offsets][:4], "... width", round(wm.width_units))

        lockups = {}
        for key, (bracket, pulse, text, open_c) in VARIANTS.items():
            # mark, transparent
            mark_svg = svg(1024, 1024, mark_group(bracket, pulse), "0 0 64 64")
            put(f"openmedgate-sygnet-{key}.svg", mark_svg)
            render_svg_png(page, mark_svg, OUT / f"openmedgate-sygnet-{key}.png", 1024, 1024)
            written.append(OUT / f"openmedgate-sygnet-{key}.png")
            # lockups, transparent
            h_svg, hw, hh = lockup_horizontal(wm, bracket, pulse, text, open_c)
            put(f"openmedgate-logo-{key}.svg", h_svg)
            render_svg_png(page, h_svg, OUT / f"openmedgate-logo-{key}.png", 2400, round(2400 * hh / hw))
            written.append(OUT / f"openmedgate-logo-{key}.png")
            s_svg, sw, sh = lockup_stacked(wm, bracket, pulse, text, open_c)
            put(f"openmedgate-logo-pion-{key}.svg", s_svg)
            render_svg_png(page, s_svg, OUT / f"openmedgate-logo-pion-{key}.png", 1600, round(1600 * sh / sw))
            written.append(OUT / f"openmedgate-logo-pion-{key}.png")
            lockups[key] = h_svg

        # tiles and avatars with backgrounds
        tiles = {
            "noc": (NIGHT, WHITE, MINT),
            "biel": ("#ffffff", NIGHT, MINT_DEEP),
            "mieta": (MINT, NIGHT, NIGHT),
        }
        for key, (bg, bracket, pulse) in tiles.items():
            t = tile(bg, bracket, pulse, 14)
            put(f"openmedgate-ikona-{key}.svg", t)
            render_svg_png(page, t, OUT / f"openmedgate-ikona-{key}.png", 1024, 1024)
            written.append(OUT / f"openmedgate-ikona-{key}.png")
            c = circle_tile(bg, bracket, pulse)
            put(f"openmedgate-awatar-{key}.svg", c)
            for size in (1024, 400):
                render_svg_png(page, c, OUT / f"openmedgate-awatar-{key}-{size}.png", size, size)
                written.append(OUT / f"openmedgate-awatar-{key}-{size}.png")

        # LinkedIn banners (PL, EN) and social square
        for lang, title, line in (
            ("pl", "Ruch na rzecz otwartych interfejsów w ochronie zdrowia", "openmedgate.com · otwarte standardy · opublikowane warunki dostępu"),
            ("en", "A movement for open interfaces in healthcare", "openmedgate.com · open standards · published terms of access"),
        ):
            render_html_png(page, banner_html(lockups["k1-mieta-bialy"], title, line, poster_b64), OUT / f"openmedgate-linkedin-baner-{lang}.png", 1584, 396)
            written.append(OUT / f"openmedgate-linkedin-baner-{lang}.png")
        render_html_png(page, social_html(lockups["k1-mieta-bialy"], poster_b64, 1080), OUT / "openmedgate-social-1080.png", 1080, 1080)
        written.append(OUT / "openmedgate-social-1080.png")

        # website: favicon, apple touch icon, OG image
        fav = svg(32, 32, f'<rect width="64" height="64" rx="14" fill="{NIGHT}"/>' + mark_group(WHITE, MINT, 0.72, 9, 9), "0 0 64 64")
        (ROOT / "static" / "favicon.svg").write_text(fav, encoding="utf-8")
        render_svg_png(page, tile(NIGHT, WHITE, MINT, 0, 0.68), ROOT / "static" / "apple-touch-icon.png", 180, 180, transparent=False)
        og = og_html(lockups["k1-mieta-bialy"], poster_b64).replace("</style>", f"@font-face{{font-family:M;font-weight:200 800;src:url(data:font/woff2;base64,{font_b64}) format('woff2')}}</style>")
        render_html_png(page, og, ROOT / "static" / "images" / "og" / "openmedgate-og.png", 1200, 630)
        browser.close()

    print(f"written {len(written)} files to {OUT}")
    if args.shared:
        shared = Path(args.shared)
        groups = {"01-Sygnety": "openmedgate-sygnet-", "02-Logotypy": "openmedgate-logo-", "03-Ikony-i-Awatary": ("openmedgate-ikona-", "openmedgate-awatar-"), "04-LinkedIn-i-Social": ("openmedgate-linkedin-", "openmedgate-social-")}
        for folder, prefixes in groups.items():
            d = shared / folder
            d.mkdir(parents=True, exist_ok=True)
            for f in written:
                if f.name.startswith(prefixes):
                    shutil.copyfile(f, d / f.name)
        print("copied to", shared)


if __name__ == "__main__":
    main()
