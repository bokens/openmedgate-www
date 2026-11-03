# Motion assets

## Hero film: `static/media/hero/open-flow.mp4`

A montage of two stock clips, chosen by the owner's decision of 2026-11-03 to use real footage instead of rendered animation.

| Segment | Clip | Source | Licence | Downloaded as |
| --- | --- | --- | --- | --- |
| 0.0 s to 6.0 s | "Heartbeat on a monitor" (patient monitor with ECG trace), Mixkit id 49226 | https://mixkit.co/free-stock-video/heartbeat-on-a-monitor-49226/ | Mixkit Stock Video Free License: free for commercial use, no attribution required, no redistribution of the clip on its own | 1280×720, 30 fps (the free tier; 4K is sold through Envato Elements) |
| 5.0 s to 12.5 s | "Bluish data center hallway", Mixkit id 23282 | https://mixkit.co/free-stock-video/bluish-data-center-hallway-23282/ | as above | 1280×720, 25 fps |
| 11.5 s to 12.5 s | clip 49226 again, from 0.5 s | | | |

Assembly (ffmpeg): each clip is scaled to 1280×720 at 30 fps and graded towards the site palette (`eq=saturation=0.82:contrast=1.05:brightness=-0.03`, `colorbalance` shifted a little away from red towards green and blue), the segments are joined with one-second cross fades, and a light vignette is applied. The last frame equals the first frame (clip 49226 at 1.5 s), so the loop is seamless. Encoded with libx264, crf 23, yuv420p, faststart; about 2.6 MB for 12.5 s. The poster `open-flow-poster.jpg` is the frame at 3 s.

Alternative clips that were downloaded and reviewed but not used: Mixkit 46365, 46368 (monitor close-ups), 23219 (data center), 31536, 32989, 31774, 12262 (abstract networks), 31563 (blood cells).

## Signatories band: `static/media/pulse/pulse-loop.mp4`

Rendered by `render_media.py pulse`: slow luminous waves over a grid. 1280×720, 24 fps, 8 s, seamless. Synthetic, no footage.

## Earlier hero renders, kept for reference

`render_media.py hero` (a network of care systems), `render_hero_pulse.py` (particle field with an ECG sweep) and `render_hero_tunnel.py` (a flythrough with gates shaped like the mark) were all rejected by the owner on 2026-11-02 and 2026-11-03. The scripts stay in this folder; their outputs are no longer in `static/`.

Posters are shown until the video plays, and always when the visitor prefers reduced motion.
