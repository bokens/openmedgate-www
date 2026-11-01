"""Render the OpenMedGate motion assets. Everything is synthetic; no footage, no patient data.

    python asset-sources/media/render_media.py hero   -> static/media/hero/open-flow.mp4 + poster
    python asset-sources/media/render_media.py pulse  -> static/media/pulse/pulse-loop.mp4 + poster

hero:  a network of care systems. Data packets travel along open interfaces; nodes breathe.
       Every motion has an integer number of cycles per loop, so the film loops seamlessly.
pulse: slow luminous waves over a grid, used behind the join band.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
FPS = 24
TAU = math.tau

MINT = (23, 227, 154)
SKY = (90, 183, 255)
WHITE = (236, 244, 248)
NIGHT_TOP = (6, 14, 22)
NIGHT_BOTTOM = (10, 26, 38)


def lerp(a, b, t):
    return a + (b - a) * t


def bezier(p0, p1, p2, u):
    x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0]
    y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1]
    return x, y


def gradient_background(w, h):
    top = np.array(NIGHT_TOP, dtype=np.float32)
    bottom = np.array(NIGHT_BOTTOM, dtype=np.float32)
    rows = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img = top[None, None, :] * (1 - rows) + bottom[None, None, :] * rows
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.62, h * 0.45
    d = np.sqrt(((xx - cx) / (w * 0.75)) ** 2 + ((yy - cy) / (h * 0.9)) ** 2)
    vignette = np.clip(1.0 - 0.55 * d ** 2, 0.35, 1.0)
    return np.clip(img * vignette[:, :, None], 0, 255)


def encode(frames_dir: Path, out_video: Path, fps: int):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required")
    out_video.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg, "-y", "-framerate", str(fps), "-i", str(frames_dir / "f_%04d.png"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(out_video),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


# ---------------------------------------------------------------- hero

HERO_W, HERO_H, SS = 1920, 1080, 2
HERO_SECONDS = 12

# Normalised node layout: (x, y, radius, kind). Kind "core" is a facility system, "node" a department, "ext" an external party.
NODES = [
    (0.56, 0.47, 30, "core"),
    (0.36, 0.30, 16, "node"), (0.40, 0.66, 15, "node"), (0.72, 0.28, 15, "node"), (0.76, 0.66, 16, "node"),
    (0.58, 0.14, 11, "node"), (0.57, 0.84, 11, "node"),
    (0.18, 0.44, 12, "ext"), (0.22, 0.80, 10, "ext"), (0.90, 0.44, 12, "ext"), (0.92, 0.82, 10, "ext"),
    (0.10, 0.18, 8, "ext"), (0.86, 0.10, 8, "ext"), (0.30, 0.10, 7, "ext"), (0.70, 0.92, 7, "ext"),
]
EDGES = [
    (0, 1, 0.08), (0, 2, -0.07), (0, 3, -0.08), (0, 4, 0.07), (0, 5, 0.05), (0, 6, -0.05),
    (1, 7, 0.06), (2, 8, -0.05), (3, 9, -0.06), (4, 10, 0.05),
    (1, 11, 0.05), (3, 12, -0.04), (1, 13, -0.04), (4, 14, 0.04), (7, 8, 0.08), (9, 10, -0.08),
    (5, 3, 0.04), (6, 2, -0.04),
]
# Packets per edge: (edge index, cycles per loop, phase, colour, size)
PACKETS = []
for i, (a, b, bend) in enumerate(EDGES):
    for k in range(2 if i < 6 else 1):
        cycles = 1 + (i % 2)
        PACKETS.append((i, cycles, (k * 0.5 + i * 0.137) % 1.0, MINT if (i + k) % 3 else SKY, 5 if i < 6 else 4))


def hero_points():
    pts = [(x * HERO_W * SS, y * HERO_H * SS) for x, y, _, _ in NODES]
    return pts


def hero_frame(t: float, bg: np.ndarray, pts) -> Image.Image:
    big = Image.new("RGB", (HERO_W * SS, HERO_H * SS), (0, 0, 0))
    draw = ImageDraw.Draw(big)
    glow = Image.new("RGB", (HERO_W, HERO_H), (0, 0, 0))
    gdraw = ImageDraw.Draw(glow)

    # Edges as faint curves
    for a, b, bend in EDGES:
        p0, p2 = pts[a], pts[b]
        mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
        dx, dy = p2[0] - p0[0], p2[1] - p0[1]
        p1 = (mx - dy * bend * 2, my + dx * bend * 2)
        line = [bezier(p0, p1, p2, u / 40) for u in range(41)]
        draw.line(line, fill=(38, 70, 86), width=2 * SS)

    # Packets
    for edge_i, cycles, phase, colour, size in PACKETS:
        a, b, bend = EDGES[edge_i]
        p0, p2 = pts[a], pts[b]
        mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
        dx, dy = p2[0] - p0[0], p2[1] - p0[1]
        p1 = (mx - dy * bend * 2, my + dx * bend * 2)
        u = (t * cycles + phase) % 1.0
        x, y = bezier(p0, p1, p2, u)
        r = size * SS
        draw.ellipse((x - r, y - r, x + r, y + r), fill=colour)
        # trail
        for k in range(1, 6):
            uu = (u - k * 0.012) % 1.0
            tx, ty = bezier(p0, p1, p2, uu)
            rr = r * (1 - k / 7)
            fade = tuple(int(c * (1 - k / 6) * 0.7) for c in colour)
            draw.ellipse((tx - rr, ty - rr, tx + rr, ty + rr), fill=fade)
        gx, gy, gr = x / SS, y / SS, size * 1.6
        gdraw.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=colour)

    # Nodes with breathing
    for i, (x, y, r0, kind) in enumerate(NODES):
        px, py = pts[i]
        breathe = 1 + 0.07 * math.sin(TAU * (t * (1 if i % 2 else 2) + i * 0.21))
        r = r0 * SS * breathe
        if kind == "core":
            draw.ellipse((px - r, py - r, px + r, py + r), outline=MINT, width=3 * SS)
            r2 = r * 0.55
            draw.ellipse((px - r2, py - r2, px + r2, py + r2), fill=MINT)
            gdraw.ellipse((px / SS - r0 * 1.3, py / SS - r0 * 1.3, px / SS + r0 * 1.3, py / SS + r0 * 1.3), fill=(12, 120, 84))
        elif kind == "node":
            draw.ellipse((px - r, py - r, px + r, py + r), outline=WHITE, width=2 * SS)
            r2 = r * 0.4
            draw.ellipse((px - r2, py - r2, px + r2, py + r2), fill=WHITE)
            gdraw.ellipse((px / SS - r0, py / SS - r0, px / SS + r0, py / SS + r0), fill=(40, 70, 90))
        else:
            draw.ellipse((px - r, py - r, px + r, py + r), fill=(120, 170, 200))

    small = big.resize((HERO_W, HERO_H), Image.Resampling.LANCZOS)
    glow = glow.filter(ImageFilter.GaussianBlur(26))
    out = bg + np.asarray(small, dtype=np.float32) + np.asarray(glow, dtype=np.float32) * 0.9
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def render_hero():
    out_dir = ROOT / "static" / "media" / "hero"
    frames = HERO_SECONDS * FPS
    bg = gradient_background(HERO_W, HERO_H)
    pts = hero_points()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for f in range(frames):
            img = hero_frame(f / frames, bg, pts)
            img.save(tmp / f"f_{f:04d}.png", compress_level=1)
            if f == 0:
                out_dir.mkdir(parents=True, exist_ok=True)
                img.save(out_dir / "open-flow-poster.jpg", quality=86)
            if f % 48 == 0:
                print(f"hero frame {f}/{frames}", flush=True)
        encode(tmp, out_dir / "open-flow.mp4", FPS)
    print("hero done", (out_dir / "open-flow.mp4").stat().st_size // 1024, "KB")


# ---------------------------------------------------------------- pulse

PULSE_W, PULSE_H, PULSE_SECONDS = 1280, 720, 8


def render_pulse():
    out_dir = ROOT / "static" / "media" / "pulse"
    frames = PULSE_SECONDS * FPS
    yy, xx = np.mgrid[0:PULSE_H, 0:PULSE_W].astype(np.float32)
    nx, ny = xx / PULSE_W, yy / PULSE_H
    base = gradient_background(PULSE_W, PULSE_H)
    grid = ((np.mod(xx, 64) < 1.2) | (np.mod(yy, 64) < 1.2)).astype(np.float32)
    d1 = np.sqrt((nx - 0.2) ** 2 + ((ny - 0.5) * 0.56) ** 2)
    d2 = np.sqrt((nx - 0.85) ** 2 + ((ny - 0.3) * 0.56) ** 2)
    mint = np.array(MINT, dtype=np.float32)
    sky = np.array(SKY, dtype=np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for f in range(frames):
            t = f / frames
            w1 = 0.5 + 0.5 * np.sin(TAU * (d1 * 2.5 - t * 2))
            w2 = 0.5 + 0.5 * np.sin(TAU * (d2 * 2.0 + t))
            field = (w1 ** 6) * np.exp(-d1 * 2.2) * 0.9 + (w2 ** 6) * np.exp(-d2 * 2.4) * 0.6
            img = base + grid[:, :, None] * (18 + 70 * field[:, :, None]) + field[:, :, None] * (mint * 0.55 + sky * 0.25)[None, None, :]
            Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(tmp / f"f_{f:04d}.png", compress_level=1)
            if f == 0:
                out_dir.mkdir(parents=True, exist_ok=True)
                Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out_dir / "pulse-poster.jpg", quality=84)
        encode(tmp, out_dir / "pulse-loop.mp4", FPS)
    print("pulse done", (out_dir / "pulse-loop.mp4").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("hero", "all"):
        render_hero()
    if which in ("pulse", "all"):
        render_pulse()
