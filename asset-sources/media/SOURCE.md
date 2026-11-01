# Motion assets

Both loops in `static/media/` are rendered by `render_media.py` in this folder. They are synthetic: no footage, no stock material, no patient data.

| File | What it shows | Size | Loop |
| --- | --- | --- | --- |
| `static/media/hero/open-flow.mp4` | a network of care systems; data packets travel along open interfaces, nodes breathe | 1920×1080, 24 fps, 12 s, H.264 | seamless, every motion has an integer number of cycles |
| `static/media/pulse/pulse-loop.mp4` | slow luminous waves over a grid, behind the signatories band | 1280×720, 24 fps, 8 s, H.264 | seamless |

Posters (`*-poster.jpg`) are the first frame of each loop and are shown until the video plays, and always when the visitor prefers reduced motion.

Re-render with `python asset-sources/media/render_media.py hero` or `pulse` (needs numpy, Pillow and ffmpeg on PATH). Colours come from the site tokens: night `#06111b`, mint `#17e39a`, sky `#5ab7ff`.
