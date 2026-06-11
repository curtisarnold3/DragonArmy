# GNSS Spoofing Aggregator

A deterministic pipeline that converts a Slingshot-style GNSS spoofing visualization MP4 into a folder of per-10-minute-step screenshots and a single aggregate density poster — same input, byte-identical output, every time.

This repository is the working prototype. It targets a vendor handoff for hardening, deployment, and scale-out.

## What's here today

✅ `pipeline/probe.py` — ffprobe wrapper, frame extractor  
✅ `pipeline/calibrate.py` — world-width NCC autocorrelation, temporal median base map  
✅ `pipeline/segment.py` — title-region diff signal → 135 window boundaries + UTC labels  
✅ `pipeline/detect.py` — luminance diff, threshold, mask, world-fold  
✅ `pipeline/aggregate.py` — presence accumulation, seam roll  
✅ `pipeline/config.yaml` — all layout constants, detection parameters, time model  
✅ Docker Compose stack: web + worker + Redis  
✅ Pinned dependencies, digest-pinned base image, bundled fonts  
✅ CI: unit tests, constraint guards (no LLM, no web imports), Docker build, in-container tests  
✅ `pipeline/render.py` — LUT colormap, gamma, 60% overlay, hourly snapshots  
✅ `pipeline/poster.py` — banner, legend, hourly grid, footer, crop  
✅ `pipeline/pipeline.py` — CLI orchestrator, progress callbacks  
✅ `api/` — FastAPI job API (POST /jobs, GET /jobs/{id}, SSE, result download)  
✅ `web/` — React + Vite + Tailwind SPA (dropzone → progress → download)

The 🚧 items are scaffolded and next in the build sequence. The detection core (Slices 0–4) is complete and golden-master tested.

## What it produces

Every run produces two artifacts:

1. **~134 PNG screenshots** — one per 10-minute window, named `step_NNN_HHMM-HHMMz.png`
2. **One aggregate density poster** — hero map at 60% overlay, colored by persistence (how many windows flagged each cell), with banner, legend, hourly preview grid, and method footer

The pipeline is classical computer vision only — no ML, no LLM, no cloud API calls in the processing path. Determinism is enforced by a golden-master CI test.

## Zero to running

### Prerequisites

- Docker + Docker Compose v2
- ~2 GB free RAM

### Bring it up

```bash
git clone git@github.com:curtisarnold3/DragonArmy.git gnss-agg
cd gnss-agg
docker compose up --build
```

### Run the CLI

```bash
python -m pipeline.pipeline input.mp4 out/
```

Produces `out/poster.png` and `out/screenshots.zip`.

## Architecture

```
┌─────────────────┐    upload     ┌─────────────────┐   enqueue   ┌─────────────────┐
│   React SPA     │ ────────────▶ │    FastAPI       │ ──────────▶ │   RQ Worker     │
│  (Vite + TW)    │ ◀──────────── │    (API)         │ ◀─ status ─ │   (pipeline)    │
└─────────────────┘  SSE / poll   └─────────────────┘    Redis    └─────────────────┘
        │  download poster + zip          │                               │
        └─────────────────────────────────┴────── volume / S3 ───────────┘
```

**Pipeline stages** (in order):

| Stage      | Module         | What it does                                                           |
|------------|----------------|------------------------------------------------------------------------|
| Probe      | `probe.py`     | Read dimensions, fps, frame count via ffprobe                          |
| Calibrate  | `calibrate.py` | NCC autocorrelation for world width; temporal median base map          |
| Segment    | `segment.py`   | Title-region diff signal → 135 window boundaries + UTC labels          |
| Detect     | `detect.py`    | Luminance diff, threshold, mask overlay graphics, fold two world copies|
| Aggregate  | `aggregate.py` | Per-pixel window count; seam roll to emptiest ocean column             |
| Render     | `render.py`    | Custom LUT, gamma 0.7, 60% overlay, 23 hourly snapshots 🚧            |
| Compose    | `poster.py`    | Banner, legend, hourly grid, footer, crop 🚧                           |
| Orchestrate| `pipeline.py`  | CLI entry point, progress callbacks 🚧                                 |

## Project layout

```
gnss-aggregator/
├── docker-compose.yml
├── docker/
│   └── Dockerfile                 # pinned base + ffmpeg + Python deps
├── pipeline/                      # pure CV — no web, no I/O surprises
│   ├── probe.py                   # ✅ ffprobe wrapper
│   ├── calibrate.py               # ✅ world width + base map
│   ├── segment.py                 # ✅ window boundaries + UTC labels
│   ├── detect.py                  # ✅ luminance diff, mask, fold
│   ├── aggregate.py               # ✅ presence accumulation + seam roll
│   ├── render.py                  # 🚧 LUT, overlay, hourly snaps
│   ├── poster.py                  # 🚧 composition
│   ├── pipeline.py                # 🚧 CLI orchestrator
│   ├── config.yaml                # all layout constants
│   └── assets/fonts/              # bundled DejaVuSans (pinned rendering)
├── api/
│   ├── main.py                    # 🚧 FastAPI endpoints
│   └── worker.py                  # 🚧 RQ task
├── web/
│   └── src/                       # 🚧 React SPA
├── tests/
│   ├── unit/                      # per-stage tests with synthetic fixtures
│   ├── golden/                    # reference MP4 (git-lfs) + expected hashes
│   └── e2e/                       # 🚧 upload→download through running API
├── requirements.txt               # fully pinned (==)
└── README.md
```

## Hard constraints

These are enforced by CI — a PR that violates them will fail automatically.

1. **No LLM in the pipeline** — `pipeline/` contains zero imports of any inference library. Checked by grep in CI on every push.
2. **Determinism** — same MP4 → byte-identical poster and aggregate array. Enforced by the golden-master test in the `test-in-container` CI job.
3. **No double-counting** — the world-fold step uses per-pixel max, never sum. Enforced by unit test asserting `presence.max() == 57` on the reference file.
4. **Frame-at-a-time memory** — the pipeline never holds more than a few frames in memory simultaneously. Target container RAM is ~1.5 GB.
5. **Config-driven layout constants** — pixel box values live in `config.yaml`, never hardcoded in source.
6. **`pipeline/` has no web dependencies** — importable and runnable with no FastAPI or Redis present. Enforced by import guard test.

## Phase plan

| Phase             | Goal                                                  | Status               |
|-------------------|-------------------------------------------------------|----------------------|
| 1 — CLI core      | Working pipeline end-to-end, golden-master CI green   | ✅ Complete — CLI green end to end |
| 2 — Job API       | FastAPI + RQ + Redis wrapping the CLI                 | 🚧 In progress (Slice 8 complete — hardening to RQ pending) |
| 3 — Frontend      | React SPA: dropzone → progress → download            | 🚧 In progress (Slice 9 complete) |
| 4 — Deploy        | Publicly reachable instance, demo-ready               | ⬜ Not started       |
| 5 — Handoff       | CONTRACTS.md, recorded walkthrough, docs current      | ⬜ Not started       |

Each phase ends with a demonstrable artifact. Transition to a hardening vendor can occur at any phase boundary.

## Running the tests

```bash
# Unit tests (no ffmpeg required)
pytest tests/unit/ -v

# Full test suite inside the pinned container (requires Docker)
docker compose build
docker run --rm gnss-agg:ci pytest tests/unit/ -v
```

The golden-master test requires the reference MP4 in `tests/golden/` via git-lfs and runs inside the container to guarantee the pinned ffmpeg version.

## Limitations and known gaps

- **Slices 5–7 not yet built** — render, poster, and CLI orchestrator are scaffolded but not implemented. The pipeline cannot produce output artifacts yet.
- **Web layer not started** — the API and SPA are Phases 2–3.
- **Single layout family** — the pipeline is tuned to the Slingshot "GNSS SPOOFING (Standard)" world-map layout. Other layouts require `config.yaml` edits and re-validation. Any MP4 that doesn't match the expected layout fails loudly with a clear error rather than producing a silently wrong poster.
- **No authentication** — this is a prototype. Production hardening (auth, S3, scaling) is scoped to Stage 1 of the vendor transition.

## Working with Claude Code on this

Each 🚧 stub is next in the slice sequence. When extending:

- **Config over code** — new layout family, new detection threshold, new time origin — all land in `config.yaml`, not in source.
- **No LLM imports in `pipeline/`** — ever. The CI grep will catch it.
- **The golden-master test is load-bearing** — a change that shifts `presence.max()` or `total_detection_pixels` requires an explicit hash update with a justification comment. Don't paper over it.
- **The poster is the product** — if a rendering choice makes the poster clearer for an analyst, that beats a technically purer approach.

## License

Prototype — internal / not for distribution.
