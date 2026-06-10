# GNSS-AGG — Decisions Log

Append-only. When code looks weird, this explains why. Never edit or delete a past entry — if a decision is reversed, append a new entry and add a `Note (post-D-NNN)` to the old one pointing forward.

---

## D-001: No LLM anywhere in the pipeline

**Decision:** The entire processing pipeline is classical CV + signal processing. No ML model, no LLM API call, no cloud inference touches the data path.

**Reasoning:** The job is deterministic image math — every stage has an exact classical answer (autocorrelation, temporal median, luminance threshold, per-pixel max). An LLM adds non-determinism, latency, cost, and an external dependency, in exchange for zero improvement in output quality. The one task that looked like it might need a model (reading timestamp text) is unnecessary because window times come from `index × 10 min` arithmetic. If text verification is ever wanted, Tesseract is the answer, not a language model.

**Implication:** "No LLM" is a hard constraint enforced by code review and CI (a grep for `anthropic`, `openai`, `langchain`, `transformers` in `pipeline/` should return zero hits). Any proposal to add model inference to the core pipeline requires a new decision entry and architectural justification.

---

## D-002: Determinism as a first-class requirement, enforced by golden-master test

**Decision:** Same input MP4 → byte-identical poster and aggregate array on every run. This is checked by a golden-master test in CI, not just asserted in documentation.

**Reasoning:** Reproducibility is a trust signal for analysts. "We ran it twice, same answer" is more credible than any number of accuracy claims. Achieving it requires: pinned dependency versions (exact `==`), a digest-pinned Docker base image, committed font files (never rely on OS copies — font hinting changes pixels), and no randomness anywhere in the code. Threading in BLAS/OpenCV affects speed only, not results.

**Implication:** Every dependency in `requirements.txt` must be pinned with `==`. The Docker base image must be pinned to a digest. The DejaVu fonts must live in `pipeline/assets/fonts/` in the repo, not installed from the OS. The golden-master test is load-bearing CI — a PR that changes the poster output must explicitly update the reference hashes with a justification comment.

---

## D-003: Config-driven layout constants, not code-driven

**Decision:** All pixel-region constants (title box, logo box, colorbar strip, crop bounds) live in `config.yaml`. Pipeline code reads the config; it does not hardcode these values or branch on layout names.

**Reasoning:** The Slingshot layout could change. When it does, the fix should be a config edit, not a code change that risks breaking the existing path. Config-driven also makes the auto-detect fallback explicit — the config states the expected value and the detection method; a mismatch fails loudly rather than silently degrading.

**Implication:** Adding a new layout family = new `config.yaml` stanza + possibly a new `source_layout` key. No `if source_layout == "X"` blocks in `pipeline/`. Mandatory check before approving any new layout: the title-box auto-detector must confirm the expected transition cadence on a sample frame.

---

## D-004: `pipeline/` is importable as a pure library with no web dependencies

**Decision:** The `pipeline/` package has no imports from `api/` or `web/`. It is runnable as a CLI (`python -m pipeline.pipeline input.mp4 out/`) with no FastAPI, Redis, or browser present.

**Reasoning:** Testability and trust. The determinism guarantee is provable only if the core can be run and tested in isolation. Entangling it with the web layer makes the golden-master test fragile and the handoff harder. The API is a thin wrapper around `pipeline.run()`; the API layer has no business touching CV logic.

**Implication:** `api/worker.py` calls `pipeline.pipeline.run()` and nothing else from `pipeline/`. If a pipeline function needs to report progress, it does so via a callback argument, not by importing from `api/`.

---

## D-005: Frame-by-frame processing, never load all frames into memory simultaneously

**Decision:** Frames are read, processed, and discarded one at a time (or in small batches for the base-map median sample). The pipeline never holds more than a few frames in memory at once.

**Reasoning:** A ~135-second 1080p video at full color is several GB uncompressed. The target container has ~1.5 GB RAM. Frame-at-a-time keeps memory flat regardless of video length.

**Implication:** `detect.py` iterates frames via the ffmpeg subprocess frame extractor and accumulates into `presence` (a single H×WW uint16 array) in place. No `frames = [read_all()]` pattern anywhere. The base-map median uses a fixed sample of 45 frames, not all frames.

---

## D-006: Seam roll to the emptiest column (lossless)

**Decision:** After folding the two world tiles, roll the composite so the map projection seam sits in the emptiest ocean column rather than mid-continent. Lossless: a NumPy roll, not a crop.

**Reasoning:** The raw seam lands at an arbitrary longitude that may bisect active spoofing regions, making the poster harder to read. Rolling to ocean is purely cosmetic and fully reversible — no data is lost, just shifted cyclically. "Emptiest column" = argmin of smoothed column energy, which is deterministic.

**Implication:** Both the background tile and the `presence` array are rolled by the same offset before rendering. The seam-column value is logged per job so the analyst can verify or unroll if needed.

---

## D-007: RQ over Celery for job queue

**Decision:** Use Redis + RQ for async job execution. For the bare MVP, start with FastAPI `BackgroundTasks` + an in-memory job dict; swap to RQ when the MVP is confirmed working.

**Reasoning:** RQ is dramatically simpler than Celery for a single-queue, single-worker use case. This pipeline has one job type, one worker, no complex routing. Celery's configuration surface is not justified. The MVP `BackgroundTasks` path lets us validate the full stack without the Redis dependency during development.

**Implication:** The swap from `BackgroundTasks` to RQ is a contained change in `api/` only; `pipeline/` is unaffected. The job status model (id → {stage, progress, result_path}) is the same either way.

---

(Append new decisions below this line, in order. Format: D-NNN, decision, reasoning, implication.)
