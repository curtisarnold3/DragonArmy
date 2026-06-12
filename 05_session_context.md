# GNSS-AGG — Session Context

## Current state
Phase: ALL PHASES COMPLETE through Phase 4 (deployed)
HEAD SHA: f780a63
Branch: main, working tree clean
Live URL: https://www.totaleclipseoftheheatmap.com
Backend: https://curtarnold.fly.dev (app: curtarnold, Fly.io)
Vercel project: dragon-army (auto-deploys from main)

## What works
- Full pipeline: upload MP4 → poster PNG + screenshots ZIP
- 40/40 unit tests passing, golden master passing (presence_max=59, total=29,539)
- Login modal with basic auth (credentials via fly secrets)
- Auto-deploy to Fly via GitHub Actions (FLY_API_TOKEN set)
- Poster always normalized to 1197px wide output

## Active bug
"No screenshot PNGs found" error on non-reference videos.
Diagnostic logging added at f780a63 — needs to be run.
Steps:
1. Deploy f780a63: cd ~/DragonArmy && git pull && fly deploy --app curtarnold
2. Upload the problematic video
3. fly logs --app curtarnold
4. Look for _extract_frames() diagnostic lines:
   - "VideoCapture opened: True/False"
   - "Frame count: N"
   - "Plan keys count: N"
   - "Loop ended at idx=N, saved=N"
5. If Plan keys count=0 → segmentation produced zero segments
6. If Frame count=0 → cv2 cannot decode the video
7. If Loop ended saved=0 but plan has keys → frame indices beyond video length

## Architecture (two-pass cv2)
Pass 1: compute_title_diffs() reads entire video → title diffs → segment boundaries
Pass 2: _extract_frames() reads video → writes ~130 representative PNGs
Then: build_base_map() + accumulate() read from cached PNGs (never re-open video)

## Key config values
tile_width: 1197 (for 2560px reference video)
detection threshold: 14.0
seam_col: 693 (confirmed)
origin_utc: 2026-06-09T00:00:00Z

## Stack
Python 3.11, cv2, numpy, scipy, Pillow
FastAPI + BackgroundTasks (in-memory job store)
React + Vite + Tailwind on Vercel
Fly.io backend (performance-2x, 4GB RAM, 10GB /data/jobs volume)

## File locations
pipeline/pipeline.py — orchestrator (two-pass)
pipeline/segment.py — title diff segmentation
pipeline/calibrate.py — base map from cached PNGs
pipeline/detect.py — luminance diff + fold
pipeline/aggregate.py — accumulate + seam roll
pipeline/render.py — LUT + hero map
pipeline/poster.py — composition
api/main.py — FastAPI endpoints + basic auth
web/src/App.jsx — React SPA with login modal
