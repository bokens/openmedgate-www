"""Render the OpenMedGate hero loop "Pulse". Everything is synthetic; no footage, no patient data.

    python asset-sources/media/render_hero_pulse.py [--seconds 16] [--preview]

A dark field of luminous particles flows along a slowly turning current, like data on the move.
An ECG trace sweeps across the lower part of the frame; every QRS complex sends out a wave that
brightens and accelerates the currents. The current and the trace are periodic by construction;
the particle layer is made seamless with a two-second crossfade at the loop seam.
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
WHITE = np.array([236, 244, 248], dtype=np.float32)
NIGHT_TOP = np.array([5, 12, 20], dtype=np.float32)
NIGHT_BOTTOM = np.array([9, 24, 36], dtype=np.float32)

# Current: curl of a sum of sines. Angular frequencies are integers so the field is periodic in tau.
FIELD = [
    # amplitude, kx, ky, omega, phase
    (0.040, 1.3, 1.0, 1, 0.3),
    (0.028, 2.2, 1.7, 1, 2.1),
    (0.016, 3.6, 2.8, 2, 4.0),
    (0.009, 5.5, 4.2, 2, 1.1),
]
DRIFT = 0.06  # units per second to the right: data moves


def background():
    rows = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = (NIGHT_TOP[None, None, :] * (1 - rows) + NIGHT_BOTTOM[None, None, :] * rows) * np.ones((1, W, 1), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # soft bokeh blobs, static
    rng = np.random.default_rng(3)
    for _ in range(9):
        cx, cy = rng.uniform(0.3, 1.05) * W, rng.uniform(0.1, 0.9) * H
        r = rng.uniform(160, 420)
        col = MINT if rng.random() < 0.6 else SKY
        blob = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))) * rng.uniform(0.03, 0.07)
        img += blob[:, :, None] * col[None, None, :]
    d = np.sqrt(((xx - W * 0.6) / (W * 0.8)) ** 2 + ((yy - H * 0.5) / (H * 0.95)) ** 2)
    vignette = np.clip(1.0 - 0.5 * d ** 2, 0.4, 1.0)
    return np.clip(img * vignette[:, :, None], 0, 255)


def velocity(x, y, tau):
    """x in [0,1.78] (aspect-corrected), y in [0,1]. Returns (u, v) in units per second."""
    u = np.full_like(x, DRIFT)
    v = np.zeros_like(y)
    for amp, kx, ky, w, ph in FIELD:
        arg = kx * x + ky * y + w * tau + ph
        c = np.cos(arg)
        u += amp * ky * c
        v -= amp * kx * c
    return u, v


def gauss(u, mu, s):
    return np.exp(-0.5 * ((u - mu) / s) ** 2)


def ecg(u):
    """One beat on u in [0,1). Returns amplitude in [-0.25, 1]."""
    return (0.12 * gauss(u, 0.18, 0.025) - 0.08 * gauss(u, 0.37, 0.008) + 1.0 * gauss(u, 0.40, 0.010)
            - 0.22 * gauss(u, 0.43, 0.009) + 0.26 * gauss(u, 0.62, 0.045))


BEATS_ACROSS = 3            # QRS complexes across the width
TRACE_Y = 0.70              # baseline height
TRACE_AMP = 150             # R peak in px
TRACE_X0, TRACE_X1 = -0.02, 1.02


def trace_points():
    xs = np.arange(int(TRACE_X0 * W), int(TRACE_X1 * W), 2)
    u = ((xs / W) * BEATS_ACROSS) % 1.0
    ys = TRACE_Y * H - TRACE_AMP * ecg(u)
    return xs, ys


def qrs_positions():
    return [((k + 0.40) / BEATS_ACROSS) for k in range(BEATS_ACROSS)]


class Particles:
    def __init__(self, n, rng):
        self.n = n
        self.x = rng.uniform(-0.04, 1.82, n)
        self.y = rng.uniform(-0.04, 1.04, n)
        self.z = rng.random(n) ** 1.6
        self.size = 0.8 + 2.2 * self.z
        self.speed = 0.5 + 0.8 * self.z
        self.bright = 0.10 + 0.70 * self.z ** 2
        kind = rng.random(n)
        self.col = np.where(kind[:, None] < 0.5, MINT[None, :], np.where(kind[:, None] < 0.9, SKY[None, :], WHITE[None, :]))
        self.px, self.py = self.x.copy(), self.y.copy()
        self.life = rng.uniform(0, 1, n)       # phase of a fade-in/out envelope
        self.life_rate = rng.uniform(0.16, 0.3, n)   # cycles per second

    def step(self, tau, dt, surge):
        self.px, self.py = self.x.copy(), self.y.copy()
        u, v = velocity(self.x, self.y, tau)
        k = dt * self.speed * (1.0 + 0.9 * surge)
        self.x += u * k
        self.y += v * k
        self.life = (self.life + self.life_rate * dt) % 1.0
        # wrap; a wrapped particle gets no trail on this frame
        wrapped = (self.x > 1.84) | (self.x < -0.06) | (self.y > 1.06) | (self.y < -0.06)
        self.x = np.where(self.x > 1.84, self.x - 1.9, self.x)
        self.x = np.where(self.x < -0.06, self.x + 1.9, self.x)
        self.y = np.where(self.y > 1.06, self.y - 1.12, self.y)
        self.y = np.where(self.y < -0.06, self.y + 1.12, self.y)
        self.px = np.where(wrapped, self.x, self.px)
        self.py = np.where(wrapped, self.y, self.py)


def beat_ages(t, period, sweep):
    """Ages (seconds) of the beats that already happened within the last few seconds."""
    ages = []
    for k in range(-2, 3):
        base = k * sweep
        for q in qrs_positions():
            tb = base + q * sweep
            age = (t - tb) % period if period else t - tb
            if 0 <= t - tb < 4.0:
                ages.append(t - tb)
    return ages


def render(seconds: int, preview: bool):
    period = float(seconds)
    sweep = period / 2.0                  # the trace head crosses the frame twice per loop
    cross = 2.0
    n_out = int(period * FPS)
    n_cross = int(cross * FPS)
    n_sim = n_out + n_cross
    rng = np.random.default_rng(11)
    parts = Particles(3000 if preview else 7000, rng)
    bg = background()
    txs, tys = trace_points()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    start_frames = []

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for f in range(n_sim):
            t = f / FPS
            tau = TAU * (t / period)
            # beats: head position sweeps left to right in `sweep` seconds
            head = (t % sweep) / sweep
            ages = []
            for k in range(-1, 3):
                for q in qrs_positions():
                    tb = (math.floor(t / sweep) + k) * sweep + q * sweep
                    if 0 <= t - tb < 4.0:
                        ages.append(t - tb)
            surge = sum(math.exp(-a * 1.8) for a in ages)
            parts.step(tau, 1.0 / FPS, surge)

            canvas = Image.new("RGB", (W, H), (0, 0, 0))
            draw = ImageDraw.Draw(canvas)
            env = 0.5 - 0.5 * np.cos(TAU * parts.life)          # fade in and out
            glow_k = 1.0 + 0.5 * surge
            b = np.clip(parts.bright * env * glow_k, 0, 1.1)
            X0 = parts.px / 1.78 * W; Y0 = parts.py * H
            X1 = parts.x / 1.78 * W; Y1 = parts.y * H
            # stretch trails a little along motion for a sense of speed
            X1s = X1 + (X1 - X0) * 0.6; Y1s = Y1 + (Y1 - Y0) * 0.6
            cols = np.clip(parts.col * b[:, None], 0, 255).astype(np.uint8)
            order = np.argsort(parts.z)
            for i in order:
                if b[i] < 0.04:
                    continue
                w = max(1, int(round(parts.size[i])))
                draw.line((float(X0[i]), float(Y0[i]), float(X1s[i]), float(Y1s[i])), fill=tuple(int(c) for c in cols[i]), width=w)

            # ECG trace: bright behind the head, fading with distance; dim ahead of it
            hx = head * W
            for i in range(len(txs) - 1):
                x = txs[i]
                behind = (hx - x) / W
                if behind < 0:
                    behind += 1.0
                k = max(0.0, 1.0 - behind / 0.8)
                k = 0.18 + 0.82 * (k ** 1.3)
                col = tuple(int(c) for c in np.clip(MINT * 0.75 * k + WHITE * 0.35 * k, 0, 255))
                draw.line((float(txs[i]), float(tys[i]), float(txs[i + 1]), float(tys[i + 1])), fill=col, width=4)
            # head
            hy = float(np.interp(hx, txs, tys))
            draw.ellipse((hx - 8, hy - 8, hx + 8, hy + 8), fill=(255, 255, 255))
            draw.ellipse((hx - 18, hy - 18, hx + 18, hy + 18), outline=(140, 255, 210), width=2)

            layer = np.asarray(canvas.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32)
            glow1 = np.asarray(canvas.filter(ImageFilter.GaussianBlur(10)), dtype=np.float32)
            glow2 = np.asarray(canvas.filter(ImageFilter.GaussianBlur(40)), dtype=np.float32)
            out = bg + layer * 0.95 + glow1 * 0.7 + glow2 * 0.28

            # shock waves from each recent beat
            for a in ages:
                k_idx = min(range(BEATS_ACROSS), key=lambda i: abs(qrs_positions()[i] * sweep - ((t - a) % sweep)))
                cx = qrs_positions()[k_idx] * W
                cy = float(np.interp(cx, txs, tys))
                r = 60 + 820 * a
                d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
                ring = np.exp(-((d - r) / (22 + 34 * a)) ** 2) * math.exp(-a * 1.6) * 0.42
                out += ring[:, :, None] * (MINT * 0.8 + WHITE * 0.2)[None, None, :]

            frame = np.clip(out, 0, 255).astype(np.uint8)
            if f < n_cross:
                start_frames.append(frame)
            if f >= n_out:
                i = f - n_out
                w = (i + 1) / (n_cross + 1)
                blended = (frame.astype(np.float32) * (1 - w) + start_frames[i].astype(np.float32) * w)
                Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8)).save(tmp / f"f_{i:04d}.png", compress_level=1)
            else:
                Image.fromarray(frame).save(tmp / f"f_{f:04d}.png", compress_level=1)
                if f == n_cross:
                    Image.fromarray(frame).save(OUT_DIR / "open-flow-poster.jpg", quality=86)
            if f % 48 == 0:
                print(f"pulse frame {f}/{n_sim}", flush=True)

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required")
        out_video = OUT_DIR / "open-flow.mp4"
        cmd = [ffmpeg, "-y", "-framerate", str(FPS), "-i", str(tmp / "f_%04d.png"),
               "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-profile:v", "high", "-tune", "film",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(out_video)]
        subprocess.run(cmd, check=True, capture_output=True)
        print("pulse done", out_video.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=16)
    ap.add_argument("--preview", action="store_true", help="fewer particles, for a quick look")
    args = ap.parse_args()
    render(args.seconds, args.preview)
