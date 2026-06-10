# GNSS-AGG — Project Spec

> The "why and what" file. A fresh chat reads this first.

## What we're building

**GNSS-AGG (GNSS Spoofing Aggregator)** is a web app that accepts a Slingshot-style GNSS-spoofing visualization MP4 and deterministically produces a folder of per-10-minute-step screenshots plus a single aggregate density poster (60% overlay, with legend, banner, and hourly preview grid).

The headline is **"same input → byte-identical output, every time"** — not "AI-powered insight generation." There is no LLM in this pipeline, anywhere, by design.

*Today vs. tomorrow:* The v1 pipeline handles the Slingshot "GNSS SPOOFING (Standard)" world-map layout now; support for other layouts can come later via config edits, not code changes.

## Who this is for

Analysts who receive these Slingshot MP4 files and need a reproducible, archivable artifact — the density poster and screenshot set — without manually scrubbing through video. Right now they screenshot frames by hand or skip the analysis entirely. This gives them a consistent, defensible output in 1–3 minutes of wall time.

What it does **not** do: interpret the geopolitical meaning of the spoofing patterns, generate written reports, or ingest any data source other than the MP4. The analyst owns the interpretation; the tool owns the extraction.

## Context

Working code is the deliverable, not a deck. The prototype needs to be demonstrable: upload an MP4, watch a progress bar, download the poster and ZIP. That's the 10-minute demo that makes the value obvious. The pipeline must be deterministic because reproducibility is a trust signal — "we ran it twice, got the same answer" is more credible than "the AI thought this."

## Core model

Classical computer vision + signal processing only. No ML, no LLM, no cloud API calls in the processing path.

- **Probe** — `ffprobe` reads dimensions, fps, frame count; validates against the known layout.
- **Calibrate** — NCC autocorrelation finds the horizontal world-wrap period (~1197 px); temporal median of sampled frames builds the clean base map.
- **Segment** — per-frame diff on the title region produces a transition signal; spikes mark 10-minute window boundaries (~135 segments).
- **Detect + fold** — each frame is diffed against the base map, luminance-thresholded, and the two tiled world-copies are folded via per-pixel max onto one canonical world.
- **Aggregate** — a boolean presence count accumulates across all windows into a per-cell integer array.
- **Render + compose** — custom LUT + alpha blend produces the hero map; Pillow draw calls add banner, legend, hourly preview grid, and footer.

**Pipeline shape.** MP4 upload → probe → calibrate → segment → detect/fold/accumulate (frame by frame, never all in memory) → render → compose → poster PNG + screenshots ZIP.

Config-driven, not code-driven. Adding support for a new layout family is a `config.yaml` edit, not an `if`-statement in source.

## Output product

Every run produces:
- **~134 PNG screenshots**, one per 10-minute window, named `step_NNN_HHMM-HHMMz.png`.
- **One aggregate density poster PNG** — hero map at 60% overlay, density legend (window-count → hours-active), banner, hourly preview grid (≈23 panels), method footer, source attribution.
- **Job log** — calibration values (world width, segment count, max persistence, total detection pixels) written per job for auditability.

No detection is dropped. Wrapped duplicate world copies are folded, not double-counted.

## Delivery stages

**Stage 1 — CLI + golden tests (immediate value):** `python -m pipeline.pipeline input.mp4 out/` runs the full pipeline and produces both deliverables. The determinism contract is locked in by the golden-master test before any web layer exists.

**Stage 2 — Web app (follow-on):** FastAPI job API + RQ worker + React SPA. Upload → progress → download. Executable in parallel once Stage 1 is green end to end.

Critically: the web layer never blocks. The CLI pipeline is the ground truth; the API just wraps it.

## Target & philosophy

- TRL target: working prototype, demonstrable end-to-end in a browser.
- Built on deliberately boring, handoff-friendly tooling: Python, ffmpeg, OpenCV, NumPy, Pillow, FastAPI, React/Vite/Tailwind, Redis/RQ, Docker Compose.
- Handoff target is a vendor or internal team that can harden, deploy, and extend without re-architecting.

## What "done" looks like for the prototype

A user drags in the reference Slingshot MP4. A progress bar advances through named stages (probe → calibrate → segment → detect → render → compose). Two download buttons appear: "Poster PNG" and "Screenshots ZIP." The poster looks right — clean base map, colored density blobs, readable legend, hourly grid. Total elapsed time under 3 minutes. The same MP4 run again produces identical files.
