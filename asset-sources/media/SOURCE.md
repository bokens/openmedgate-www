# Motion assets

Both loops in `static/media/` are rendered by scripts in this folder. They are synthetic: no footage, no stock material, no patient data.

| File | Script | What it shows | Size | Loop |
| --- | --- | --- | --- | --- |
| `static/media/hero/open-flow.mp4` | `render_hero_pulse.py` | a dark field of luminous particles flowing along a slowly turning current; an ECG trace sweeps across the lower part of the frame and every QRS complex sends out a wave that brightens and accelerates the currents | 1920×1080, 24 fps, 16 s, H.264 | the current and the trace are periodic by construction; the particle layer is made seamless with a two-second crossfade at the seam |
| `static/media/pulse/pulse-loop.mp4` | `render_media.py pulse` | slow luminous waves over a grid, behind the signatories band | 1280×720, 24 fps, 8 s, H.264 | seamless |

`render_media.py hero` renders the earlier hero loop (a network of care systems) and is kept for reference.

Posters (`*-poster.jpg`) are a frame of each loop and are shown until the video plays, and always when the visitor prefers reduced motion.

Re-render with `python asset-sources/media/render_hero_pulse.py` (`--preview` renders fewer particles for a quick look) or `python asset-sources/media/render_media.py pulse`. Both need numpy, Pillow and ffmpeg on PATH. Colours come from the site tokens: night `#06111b`, mint `#17e39a`, sky `#5ab7ff`.
