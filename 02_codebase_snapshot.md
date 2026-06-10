# GNSS-AGG — Codebase Snapshot

> The "what physically exists" file. Stack, layout, data model, and an honest ✅/🚧 ledger. Update when reality changes, not when you intend to.

## Stack

**Boring on purpose.**

- **Python 3.11** — all pipeline and API code
- **ffmpeg / ffprobe (system binary, pinned version in Dockerfile)** — video decode and frame extraction
- **opencv-python-headless** — NCC autocorrelation, frame diff; no GUI deps
- **numpy** — all array math; temporal median, accumulation, LUT application
- **scipy** — smoothing kernel for seam-roll column energy
- **Pillow** — poster composition, text draw, PNG encode
- **FastAPI + Uvicorn** — HTTP API
- **Redis + RQ** — async job queue (BackgroundTasks for bare MVP, swap to RQ for production)
- **React + Vite + TailwindCSS** — single-page frontend
- **Docker + docker-compose** — three services: `web`, `worker`, `redis`
- **No ORM** (deliberate — plain file I/O and temp workspaces, nothing to migrate)
- **No LLM / ML API** (hard constraint — classical CV only)

## Repository

`gnss-aggregator/` (local, not yet pushed to remote).
Branch: `main`. Working tree clean at project start (no commits yet — Slice 0 is the first).

## Directory layout

```
gnss-aggregator/
├─ docker-compose.yml
├─ docker/
│  └─ Dockerfile                    # 🚧 stub — pinned base + ffmpeg + Python deps
├─ pipeline/                        # pure CV — no web, no I/O surprises
│  ├─ probe.py                      # 🚧 ffprobe wrapper; validates dimensions/fps
│  ├─ calibrate.py                  # 🚧 world-width NCC + temporal median base map
│  ├─ segment.py                    # 🚧 title-region diff signal → boundaries + UTC labels
│  ├─ detect.py                     # 🚧 frame diff, threshold, mask, fold
│  ├─ aggregate.py                  # 🚧 presence accumulation + seam roll
│  ├─ render.py                     # 🚧 LUT + gamma + 60% overlay + hourly snaps
│  ├─ poster.py                     # 🚧 banner, legend, stats, hourly grid, crop, footer
│  ├─ pipeline.py                   # 🚧 orchestrates stages 1→14, progress callbacks
│  ├─ config.yaml                   # 🚧 all tuned constants (§5 of spec)
│  └─ assets/fonts/                 # 🚧 DejaVuSans.ttf + DejaVuSans-Bold.ttf (committed)
├─ api/
│  ├─ main.py                       # 🚧 FastAPI: POST /jobs, GET /jobs/{id}, SSE /jobs/{id}/events
│  └─ worker.py                     # 🚧 RQ task wrapping pipeline.run()
├─ web/
│  └─ src/                          # 🚧 React SPA: dropzone → progress → preview → downloads
├─ tests/
│  ├─ unit/                         # 🚧 per-stage tests with tiny synthetic fixtures
│  ├─ golden/                       # 🚧 reference MP4 (git-lfs) + expected hashes file
│  └─ e2e/                          # 🚧 upload→download through the running API
├─ requirements.txt                 # 🚧 fully pinned (==)
└─ README.md
```

## Data model

```
MP4 upload (temp workspace per job)
       ↓
probe results (dict: width, height, fps, nb_frames)
       ↓
base_map.npy  (H × WW uint8, per-pixel temporal median)
world_width   (int, NCC autocorrelation result)
       ↓
segments[]    (list of {start_frame, end_frame, rep_frame, utc_start, utc_end})
       ↓
presence.npy  (H × WW uint16, per-pixel window count)
       ↓
poster.png    (final composed artifact)
screenshots/  (folder of ~134 PNGs)
screenshots.zip
```

No database. Each job lives entirely in a temp directory; the API serves files from there (or uploads to S3 for production). Nothing leaks between jobs.

## What works today

- ✅ Nothing yet — this is the project-start snapshot. Slice 0 (scaffold) is the first commit.

## What's stubbed (work items, in slice order)

**Slice 0 — Scaffold (first):**
- 🚧 `Dockerfile` with pinned ffmpeg + Python deps
- 🚧 `docker-compose.yml` (web + worker + redis)
- 🚧 `requirements.txt` fully pinned
- 🚧 CI that builds the image and runs an empty test suite

**Slice 1 — Video primitives:**
- 🚧 `probe.py` — `ffprobe` wrapper, frame-grabber using ffmpeg subprocess
- Unit tests: read a tiny fixture clip, return correct dimensions/fps, extract a specific frame as NumPy array

**Slice 2 — Calibration:**
- 🚧 `calibrate.py` — NCC autocorrelation for world width; temporal median base map; logo-box paint-out
- Accept criterion: returns width 1197 on the reference MP4; logo box matches ocean color

**Slice 3 — Segmentation + time model:**
- 🚧 `segment.py` — title-region diff signal → boundary detection; index→UTC arithmetic
- Accept criterion: 135 segments, window 1 = `00:00–01:30Z`, window 134 = `22:10–23:40Z`

**Slice 4 — Detection core (the golden one, load-bearing):**
- 🚧 `detect.py` — frame diff, BGR luminance weights, threshold, mask, fold (per-pixel max)
- 🚧 `aggregate.py` — presence accumulation, seam roll (emptiest column)
- Accept criterion: `presence.max() == 57`, total detection pixels ≈ 29,538, array hash matches reference

**Slice 5 — Rendering:**
- 🚧 `render.py` — custom 6-stop LUT, gamma 0.7, 60% overlay blend, 23 hourly snaps
- Accept criterion: hero map + hourly PNGs match reference hashes

**Slice 6 — Poster composition:**
- 🚧 `poster.py` — banner, legend (window→hours ticks), stats block, hourly grid, footer, crop
- Accept criterion: renders at expected size, no label collisions, no title ghost, pixel-matches reference

**Slice 7 — Packaging + CLI:**
- 🚧 `pipeline.py` — orchestrates stages 1→14 with progress callbacks; writes poster + screenshots ZIP
- Accept criterion: `python -m pipeline.pipeline ref.mp4 out/` produces both deliverables end to end

**Slice 8 — Job API:**
- 🚧 `api/main.py` + `api/worker.py` — POST /jobs, status polling/SSE, result download
- Accept criterion: POST returns id, status advances through named stages, files served at result endpoint

**Slice 9 — Frontend:**
- 🚧 `web/src/` — dropzone, progress bar (SSE/poll), poster preview, two download buttons
- Accept criterion: user can upload → watch progress → download both artifacts in a browser

**Slice 10 — Containerize + deploy:**
- 🚧 `docker-compose.yml` all three services; e2e test against running stack
- Accept criterion: e2e test passes against deployed URL

**Dropped from roadmap:**
- Tesseract OCR for timestamp verification — unnecessary; index × 10 min is sufficient and deterministic
- Any ML model for blob classification — classical threshold is sufficient and deterministic

## Configuration philosophy

Adding support for a new layout family = edit `config.yaml` (new pixel boxes for title/logo/colorbar) + possibly a new `source_layout` key. Never an `if`-statement in pipeline source. Mandatory pre-adoption check before any new layout: "does the title box auto-detector confirm the expected cadence on a sample frame?" If not, fail loudly with a clear error, don't produce a silently wrong poster.
