# GNSS-AGG — Unified Roadmap

> The "sequenced plan" file. A phase without a checkable exit criterion is a wish, not a plan.

---

## Phase 1 — Scaffold & CLI Core  ⬜ not started

**Goal:** Produce a working CLI pipeline that runs end to end on the reference MP4 and passes the golden-master determinism test — with no web layer yet.

**Work items (in slice order):**
- Slice 0: Repo scaffold, pinned deps, Dockerfile, docker-compose, empty CI — ⬜
- Slice 1: `probe.py` + frame-extractor wrapper — ⬜
- Slice 2: `calibrate.py` — world-width NCC + temporal median base map — ⬜
- Slice 3: `segment.py` — title-region diff signal → 135 boundaries + UTC labels — ⬜
- Slice 4: `detect.py` + `aggregate.py` — detection, fold, accumulation, seam roll — ⬜ **[golden-master anchor]**
- Slice 5: `render.py` — LUT, gamma, 60% overlay, 23 hourly snaps — ⬜
- Slice 6: `poster.py` — full composition, banner, legend, crop — ⬜
- Slice 7: `pipeline.py` — orchestrator + progress callbacks + CLI entry point — ⬜

**Dependencies:** Reference MP4 in `tests/golden/` via git-lfs. Docker build succeeds (Slice 0 exit criterion).

**Exit criterion:** `python -m pipeline.pipeline tests/golden/ref.mp4 out/` produces a poster PNG and screenshots ZIP, and the golden-master CI test reports `presence.max() == 57`, total detection pixels ≈ 29,538, and poster hash matches reference — on two consecutive runs with identical hashes.

---

## Phase 2 — Job API  ⬜ not started

**Goal:** Wrap the CLI pipeline in an async HTTP API so that uploads can be submitted and results retrieved without running the CLI manually.

**Work items (priority order):**
1. Slice 8: FastAPI + BackgroundTasks (MVP) → RQ + Redis (production swap)
   - `POST /jobs` — accept MP4 upload, return job id
   - `GET /jobs/{id}` — return status (stage name + % complete)
   - `GET /jobs/{id}/events` — SSE stream of progress
   - `GET /jobs/{id}/result/poster` and `/result/zip` — serve artifacts

**Dependencies:** Phase 1 exit criterion met (CLI green end to end).

**Exit criterion:** `curl -F file=@ref.mp4 http://localhost:8000/jobs` returns a job id; polling `GET /jobs/{id}` shows stage progression; artifacts downloadable at result endpoints. All confirmed by an automated API test against the running container.

---

## Phase 3 — Frontend  ⬜ not started

**Goal:** A browser UI so a non-technical analyst can use the tool without touching a terminal.

**Work items:**
1. Slice 9: React + Vite + Tailwind SPA
   - Dropzone (MP4 only, size guard)
   - Progress bar driven by SSE or polling
   - Poster preview (scaled, in-browser)
   - Two download buttons: "Poster PNG" and "Screenshots ZIP"

**Dependencies:** Phase 2 exit criterion met (API endpoints working).

**Exit criterion:** An analyst uploads the reference MP4 via the browser, watches stage-named progress, and downloads both artifacts — unassisted, in under 5 minutes of wall time.

---

## Phase 4 — Demo-ready (user-facing milestone)  ⬜ not started

**Goal:** A deployed, publicly reachable instance that a stakeholder can use in a live demo without local setup.

**Work items:**
- Slice 10: Containerize all three services; e2e test against deployed URL
- Choose deployment target (Fly.io / Render / VPS)
- Wire up S3-compatible storage for job artifacts (or confirm local volume is acceptable for demo scale)
- Final QA: run the reference MP4 on the deployed instance twice and confirm identical poster hashes

**Dependencies:** Phase 3 exit criterion met. Deployment target decided.

**Exit criterion:** A stakeholder navigates to the public URL, uploads the reference MP4, receives the poster and ZIP, and the experience takes under 5 minutes from drop to download. The same file run a second time produces identical artifacts. No local install required.

---

## Phase 5 — Handoff package  ⬜ not started

**Goal:** Produce the artifacts that make a handoff to a vendor or internal team credible and low-risk.

**Work items:**
- Updated README with architecture diagram, dependency versions, and deployment instructions
- `CONTRACTS.md` in the repo mirroring the hard constraints from the working rules
- Golden-master test documented as the "do not break this" CI gate
- `config.yaml` fully commented (every constant, its source, its auto-detect fallback)
- One recorded walkthrough: upload → poster in real time, narrated
- Decision log current through handoff date

**Exit criterion:** A developer who has never seen the project can clone the repo, run `docker compose up`, upload the reference MP4 via browser, receive the correct poster, and the golden-master CI test passes — all within 30 minutes of reading the README, with no help from the original author.

---

## Transition / scale stages (post-handoff)

**Stage 1 — Hardening (weeks 1–4):** Vendor reviews `CONTRACTS.md` and hard constraints; adds authentication layer; sets up production S3 bucket; onboards ops team to the golden-master CI gate.

**Stage 2 — Extension (parallel, weeks 2–8):** Additional layout families added via `config.yaml`; job history and user management; optional LLM-generated caption post-step (bolt-on, isolated from deterministic core).

---

## Cross-cutting concerns (track throughout)

- **Font pinning** — DejaVu fonts must be committed to the repo before any poster rendering is validated. A missing font is a silent determinism break.
- **ffmpeg version pinning** — frame-decode behavior can change between ffmpeg versions. The Dockerfile must pin a specific version; any upgrade requires re-running the golden-master test and updating reference hashes deliberately.
- **Layout-mismatch loud failure** — any MP4 that doesn't match the expected Slingshot layout must produce a clear error, not a silently wrong poster. This is a UX and trust constraint.
- **CEO day-job constraints** — this project gets built in sprint-sized chunks between other obligations. Each slice must be independently completable in a single session.

---

## Dependency graph summary

```
Slice 0 → Slice 1 → Slice 2 → Slice 3 → Slice 4 (golden) → Slice 5 → Slice 6 → Slice 7
                                                                                      │
                                                                               Phase 1 done
                                                                                      │
                                                                              Phase 2 (API)
                                                                                      │
                                                                           Phase 3 (Frontend)
                                                                                      │
                                                                              Phase 4 (Deploy)
                                                                                      │
                                                                           Phase 5 (Handoff) ←── parallel from Phase 4
```

**Single highest-leverage unblocker:** The Slice 4 golden-master test. Once `presence.max() == 57` and total detection pixels ≈ 29,538 are confirmed and locked in CI, the entire rendering and composition path can proceed with confidence. Everything downstream of Slice 4 is presentation math, not correctness math.
