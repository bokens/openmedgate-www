"""Render the OpenMedGate hero loop "Przelot" (flythrough). Synthetic; no footage, no patient data.

    python asset-sources/media/render_hero_tunnel.py [--seconds 12] [--preview]

The camera flies along a corridor of luminous data particles. Straight ahead a glowing ECG ribbon
runs into the distance and passes through gates shaped like the OpenMedGate mark. Light packets
travel along the ribbon towards the viewer. Each time the camera crosses a gate, a beat: a flash
and a wave. The scene is periodic along the flight axis, so the loop is seamless by construction.
"""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "static" / "media" / "hero"
W, H, FPS = 1920, 1080, 24
TAU = math.tau

MINT = np.array([23, 227, 154], dtype=np.float32)
SKY = np.array([90, 183, 255], dtype=np.float32)
WHITE = np.array([240, 246, 250], dtype=np.float32)
NIGHT_TOP = np.array([4, 10, 18], dtype=np.float32)
NIGHT_BOTTOM = np.array([8, 22, 34], dtype=np.float32)

L = 60.0            # corridor period along z (world units)
GATE_SPACING = 20.0  # three gates per loop
VP = (0.67, 0.52)    # vanishing point on screen (keeps the left side free for the headline)


def gauss(u, mu, s):
    return np.exp(-0.5 * ((u - mu) / s) ** 2)


def ecg(u):
    """One beat on u in [0,1)."""
    return (0.12 * gauss(u, 0.18, 0.025) - 0.08 * gauss(u, 0.37, 0.008) + 1.0 * gauss(u, 0.40, 0.010)
            - 0.22 * gauss(u, 0.43, 0.009) + 0.26 * gauss(u, 0.62, 0.045))


def fog(z):
    return np.exp(-z / 14.0)


def background(cx, cy):
    rows = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = (NIGHT_TOP[None, None, :] * (1 - rows) + NIGHT_BOTTOM[None, None, :] * rows) * np.ones((1, W, 1), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    glow = np.exp(-(d / (0.30 * H)) ** 2)
    img += glow[:, :, None] * (MINT * 0.16 + SKY * 0.06)[None, None, :]
    vignette = np.clip(1.0 - 0.45 * ((xx - W / 2) / (W * 0.75)) ** 2 - 0.5 * ((yy - H / 2) / (H * 0.8)) ** 2, 0.35, 1.0)
    return np.clip(img * vignette[:, :, None], 0, 255), d


# Mark geometry in gate space (units of the 64 grid, centred at 32), as line segments.
MARK_SEGMENTS = [
    ((23, 11), (11, 11)), ((11, 11), (11, 24)), ((11, 40), (11, 53)), ((11, 53), (23, 53)),
    ((41, 11), (53, 11)), ((53, 11), (53, 24)), ((53, 40), (53, 53)), ((53, 53), (41, 53)),
]
GATE_SIZE = 5.0   # half-size of the gate in world units
RIBBON_Y = 1.15   # screen y grows downwards: the ECG ribbon runs below eye level, like a lit road
RIBBON_AMP = 0.75  # spikes rise towards the centre of the view


class Scene:
    def __init__(self, n, rng):
        self.n = n
        self.r = 1.3 + 8.5 * rng.random(n) ** 0.75
        self.ang = rng.uniform(0, TAU, n)
        self.z0 = rng.uniform(0, L, n)
        self.phase = rng.uniform(0, TAU, n)
        self.size = 0.8 + 2.2 * rng.random(n) ** 1.5
        self.base = 0.35 + 0.65 * rng.random(n) ** 1.2
        kind = rng.random(n)
        self.col = np.where(kind[:, None] < 0.55, MINT[None, :], np.where(kind[:, None] < 0.9, SKY[None, :], WHITE[None, :]))
        self.prev = None  # previous projection (X, Y, zrel)
        self.packets_z0 = rng.uniform(0, L, 14)

    def positions(self, t, T):
        # a gentle periodic sway instead of an orbit: motion stays almost purely radial on screen
        ang = self.ang + 0.16 * np.sin(TAU * t / T + self.phase)
        x = self.r * np.cos(ang)
        y = self.r * np.sin(ang) * 0.62  # flattened corridor, wider than tall
        return x, y


def project(x, y, zrel, cam, f, cx, cy):
    cam_x, cam_y, roll = cam
    dx, dy = x - cam_x, y - cam_y
    c, s = math.cos(roll), math.sin(roll)
    rx, ry = dx * c - dy * s, dx * s + dy * c
    return cx + f * rx / zrel, cy + f * ry / zrel


def render(seconds: int, preview: bool):
    T = float(seconds)
    v = L / T
    f = 0.95 * H
    cx, cy = VP[0] * W, VP[1] * H
    rng = np.random.default_rng(5)
    scene = Scene(2500 if preview else 5500, rng)
    bg, dist = background(cx, cy)
    n_frames = int(T * FPS)
    gate_zs = [10.0, 30.0, 50.0]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for fi in range(n_frames):
            t = fi / FPS
            zc = v * t
            cam = (0.3 * math.sin(TAU * t / T), 0.14 * math.sin(2 * TAU * t / T + 1.0), 0.012 * math.sin(TAU * t / T + 0.6))
            # beat: age since the camera crossed the nearest gate behind it
            age = min(((zc - g) % L) for g in gate_zs) / v
            flash = math.exp(-age * 2.6)

            canvas = Image.new("RGB", (W, H), (0, 0, 0))
            draw = ImageDraw.Draw(canvas)

            # ---- particles
            x, y = scene.positions(t, T)
            zrel = (scene.z0 - zc) % L
            visible = (zrel > 0.35) & (zrel < 52)
            X, Y = project(x, y, np.maximum(zrel, 0.35), cam, f, cx, cy)
            b = scene.base * fog(zrel) * (1.0 + 0.9 * flash)
            size = np.clip(f * 0.011 * scene.size / zrel, 0.8, 9)
            if scene.prev is None:
                scene.prev = (X.copy(), Y.copy(), zrel.copy())
            Xp, Yp, zp = scene.prev
            wrapped = zrel > zp  # went behind the camera and reappeared far away
            order = np.argsort(-zrel)
            for i in order:
                if not visible[i] or b[i] < 0.02:
                    continue
                col = tuple(int(c) for c in np.clip(scene.col[i] * min(b[i], 1.15), 0, 255))
                w = max(1, int(round(size[i])))
                if wrapped[i]:
                    draw.ellipse((X[i] - w / 2, Y[i] - w / 2, X[i] + w / 2, Y[i] + w / 2), fill=col)
                else:
                    # stretch the trail a little for speed
                    ex, ey = X[i] + (X[i] - Xp[i]) * 0.5, Y[i] + (Y[i] - Yp[i]) * 0.5
                    draw.line((float(Xp[i]), float(Yp[i]), float(ex), float(ey)), fill=col, width=w)
            scene.prev = (X.copy(), Y.copy(), zrel.copy())

            # ---- ECG ribbon ahead of the camera
            zs = np.arange(1.7, 48.0, 0.12)
            zw = zc + zs
            u = ((zw - 2.0) / GATE_SPACING) % 1.0      # QRS sits two units beyond each gate
            ry = RIBBON_Y - RIBBON_AMP * ecg(u)
            RX, RY = project(np.zeros_like(zs), ry, zs, cam, f, cx, cy)
            rb = np.minimum(fog(zs) * 1.35 + 0.08, 1.0) * (1.0 + 0.6 * flash)
            rw = np.clip(f * 0.012 / zs, 2, 12)
            for i in range(len(zs) - 1, 0, -1):
                k = min(rb[i] * 1.3, 1.0)
                col = tuple(int(c) for c in np.clip(MINT * k * 0.95 + WHITE * k * 0.35 * (1 - zs[i] / 48), 0, 255))
                draw.line((float(RX[i]), float(RY[i]), float(RX[i - 1]), float(RY[i - 1])), fill=col, width=int(round(rw[i])))

            # ---- packets travelling along the ribbon towards the viewer
            pz = (scene.packets_z0 - 2 * v * t) % L
            for z in sorted(pz, reverse=True):
                if z < 1.7 or z > 48:
                    continue
                uu = ((zc + z - 2.0) / GATE_SPACING) % 1.0
                PX, PY = project(np.array([0.0]), np.array([RIBBON_Y - RIBBON_AMP * float(ecg(np.array([uu]))[0])]), np.array([z]), cam, f, cx, cy)
                r = float(np.clip(f * 0.014 / z, 2, 16))
                draw.ellipse((PX[0] - r, PY[0] - r, PX[0] + r, PY[0] + r), fill=(255, 255, 255))

            # ---- gates (the mark) along the corridor
            for g in gate_zs:
                zg = (g - zc) % L
                if zg < 0.5 or zg > 50:
                    continue
                near = math.exp(-max(zg - 1.0, 0) / 3.0)
                k = min(fog(zg) * 2.4 * (1 + 0.8 * near) + 0.18, 1.0)
                wline = int(np.clip(f * 0.05 / zg, 2, 30))
                col = tuple(int(c) for c in np.clip(WHITE * k * (0.8 + 0.2 * near) + MINT * 0.3 * near, 0, 255))
                for (ax, ay), (bx, by) in MARK_SEGMENTS:
                    px = np.array([(ax - 32) / 32 * GATE_SIZE, (bx - 32) / 32 * GATE_SIZE])
                    py = np.array([-(ay - 32) / 32 * GATE_SIZE, -(by - 32) / 32 * GATE_SIZE])
                    GX, GY = project(px, py, np.array([zg, zg]), cam, f, cx, cy)
                    draw.line((float(GX[0]), float(GY[0]), float(GX[1]), float(GY[1])), fill=col, width=wline)

            layer = np.asarray(canvas, dtype=np.float32)
            glow1 = np.asarray(canvas.filter(ImageFilter.GaussianBlur(10)), dtype=np.float32)
            glow2 = np.asarray(canvas.filter(ImageFilter.GaussianBlur(42)), dtype=np.float32)
            out = bg * (1 + 0.35 * flash) + layer + glow1 * 0.75 + glow2 * 0.35

            # ---- beat wave from the vanishing point
            if age < 1.6:
                r = 40 + 1500 * age
                ring = np.exp(-((dist - r) / (30 + 60 * age)) ** 2) * math.exp(-age * 2.2) * 0.55
                out += ring[:, :, None] * (MINT * 0.8 + WHITE * 0.2)[None, None, :]

            frame = np.clip(out, 0, 255).astype(np.uint8)
            Image.fromarray(frame).save(tmp / f"f_{fi:04d}.png", compress_level=1)
            if fi == int(n_frames * 0.22):
                Image.fromarray(frame).save(OUT_DIR / "open-flow-poster.jpg", quality=86)
            if fi % 48 == 0:
                print(f"tunnel frame {fi}/{n_frames}", flush=True)

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required")
        out_video = OUT_DIR / "open-flow.mp4"
        subprocess.run([ffmpeg, "-y", "-framerate", str(FPS), "-i", str(tmp / "f_%04d.png"),
                        "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-profile:v", "high", "-tune", "film",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(out_video)], check=True, capture_output=True)
        print("tunnel done", out_video.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=12)
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    render(args.seconds, args.preview)
