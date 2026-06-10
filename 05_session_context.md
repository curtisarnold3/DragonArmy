# GNSS-AGG — Session Context

> The "where are we right now" file. Most volatile of the six — rewrite it freely.

## Current state (start of new chat)

**Phase:** Phase 1 — Scaffold & CLI Core ⬜ not started.

**Repository:** Not yet initialized. No commits. Working tree does not exist yet.

**Last completed work:**
- None. This is the project-start state. The six knowledge files are the first artifact.

**Pipeline / app state at last check:** Nothing running. No Docker image built. No reference MP4 ingested yet.

## What's next (immediate)

**Sprint: Slice 0 — Scaffold**

1. Initialize the repo: `gnss-aggregator/`, git init, initial commit of README + `.gitignore`.
2. Write `requirements.txt` with all deps fully pinned (`==`): `opencv-python-headless`, `numpy`, `scipy`, `Pillow`, `fastapi`, `uvicorn`, `rq`, `redis`, `httpx` (for e2e tests), `pytest`. Include a comment noting the ffmpeg system binary version.
3. Write `docker/Dockerfile`: pinned Python 3.11 base image (by digest), install ffmpeg at a fixed version, copy `requirements.txt`, `pip install -r requirements.txt`.
4. Write `docker-compose.yml`: three services — `web` (FastAPI), `worker` (RQ), `redis` (official pinned image).
5. Create an empty `tests/` structure with a placeholder test that always passes.
6. Confirm CI runs: `docker compose build` succeeds, empty test suite is green.

**Before this sprint starts:** No blocking decisions outstanding. CEO needs to provide the reference MP4 and drop it into `tests/golden/` via git-lfs once the repo exists.

**Exit criterion for Slice 0:** `docker compose build` succeeds with no errors. `pytest tests/` passes (even if the only test is `assert True`). This is confirmed by Claude Code's per-commit report.

## Backlog (deferred until Slice 0 completes)

Ordered by slice sequence:

1. Slice 1 — Video primitives (`probe.py` + frame extractor)
2. Slice 2 — Calibration (`calibrate.py`)
3. Slice 3 — Segmentation + time model (`segment.py`)
4. Slice 4 — Detection core — **golden-master anchor**
5. Slice 5 — Rendering (`render.py`)
6. Slice 6 — Poster composition (`poster.py`)
7. Slice 7 — Packaging + CLI (`pipeline.py`)
8. Slice 8 — Job API (`api/`)
9. Slice 9 — Frontend (`web/`)
10. Slice 10 — Containerize + deploy

Dropped from roadmap: Tesseract OCR for timestamp verification; any ML inference in the pipeline.

## Open questions / unresolved

- **Reference MP4 location** — CEO needs to provide the Slingshot source file and set up git-lfs in the repo before Slice 1 can be validated. Not blocking Slice 0.
- **Deployment target** — Fly.io vs Render vs VPS not yet decided. Not blocking any slice before 10.
- **S3 vs local volume for job artifacts** — MVP uses local volume. Production target unresolved. Not blocking before Slice 8.

## Active risks being tracked

- **Font hinting divergence** — if DejaVu fonts are not committed to the repo and instead pulled from the OS, poster pixel output will vary across environments. Mitigation: commit `DejaVuSans.ttf` and `DejaVuSans-Bold.ttf` into `pipeline/assets/fonts/` in Slice 0 or Slice 6 at the latest.
- **ffmpeg version drift** — if the Dockerfile installs `ffmpeg` without pinning the version, a base-image update could change frame-decode behavior. Mitigation: pin ffmpeg to an explicit version in the Dockerfile; document the version in a comment in `requirements.txt`.
- **Slingshot layout change** — if the overlay template is restyled, the pixel-box constants break. Mitigation: D-003 config discipline + loud failure on layout mismatch.

## Quick orientation for a fresh chat

Read the other five knowledge files in this order:
1. `01_project_spec.md` — what we're building and why
2. `02_codebase_snapshot.md` — what exists, what's stubbed
3. `03_decisions_log.md` — why things are the way they are
4. `04_working_rules.md` — how we operate
5. `06_unified_roadmap.md` — the sequenced phase plan

Then re-read this file for current state.

**Verification before proposing work:** name the current phase, name what's next, name one decision, name one stub, and state where that stub sits in the roadmap.
