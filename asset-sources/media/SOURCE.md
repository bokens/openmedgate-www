# Motion assets

Both loops in `static/media/` are rendered by scripts in this folder. They are synthetic: no footage, no stock material, no patient data.

| File | Script | What it shows | Size | Loop |
| --- | --- | --- | --- | --- |
| `static/media/hero/open-flow.mp4` | `render_hero_tunnel.py` | a flight along a corridor of luminous data particles; ahead, a glowing ECG ribbon runs into the distance below eye level and passes through gates shaped like the OpenMedGate mark; light packets travel along the ribbon towards the viewer; every crossing of a gate gives a flash and a wave | 1920×1080, 24 fps, 12 s, H.264 | the scene is periodic along the flight axis (three gates per loop), so the loop is seamless by construction |
| earlier hero: `render_hero_pulse.py` | kept for reference | a flat field of particles with an ECG trace sweeping across | 1920×1080, 16 s | crossfade at the seam |
| `static/media/pulse/pulse-loop.mp4` | `render_media.py pulse` | slow luminous waves over a grid, behind the signatories band | 1280×720, 24 fps, 8 s, H.264 | seamless |

`render_media.py hero` renders the earlier hero loop (a network of care systems) and is kept for reference.

Posters (`*-poster.jpg`) are a frame of each loop and are shown until the video plays, and always when the visitor prefers reduced motion.

Re-render with `python asset-sources/media/render_hero_pulse.py` (`--preview` renders fewer particles for a quick look) or `python asset-sources/media/render_media.py pulse`. Both need numpy, Pillow and ffmpeg on PATH. Colours come from the site tokens: night `#06111b`, mint `#17e39a`, sky `#5ab7ff`.
