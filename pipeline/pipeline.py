"""CLI orchestrator for GNSS Spoofing Aggregator pipeline."""

import logging
import zipfile
import yaml
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def run(mp4_path, output_dir, progress_callback=None) -> dict:
    mp4_path = Path(mp4_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir = output_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    import os
    if os.path.exists("/data/jobs"):
        import tempfile
        work_dir = Path(tempfile.mkdtemp(
            prefix="gnss_job_", dir="/data/jobs"))
    else:
        import tempfile
        work_dir = Path(tempfile.mkdtemp(prefix="gnss_job_"))

    def progress(stage, pct):
        if progress_callback:
            progress_callback(stage, pct)
        logger.info(f"[{pct:3d}%] {stage}")

    with open(Path(__file__).parent / "config.yaml") as f:
        config = yaml.safe_load(f)

    # ── PASS 1: Sequential decode → title diffs → segments ──
    progress("segment", 5)
    from pipeline.segment import (
        compute_title_diffs,
        find_segment_boundaries,
        assign_times,
    )
    diffs = compute_title_diffs(mp4_path, config)
    threshold = config["segmentation"]["transition_threshold"]
    seg_tuples = find_segment_boundaries(diffs, threshold)
    segments = assign_times(seg_tuples, config)
    logger.info(f"Found {len(segments)} segments")
    progress("segment", 20)

    # ── PASS 2: Sequential decode → write 135 PNGs ──
    progress("screenshots", 25)
    _extract_frames(mp4_path, segments, screenshots_dir, config)
    progress("screenshots", 45)

    # ── Base map from cached PNGs ──
    progress("base_map", 50)
    from pipeline.calibrate import build_base_map, find_world_width
    base_map = build_base_map(screenshots_dir, config)

    # Measure world width from base map (confirms WW=1197)
    ww = find_world_width(base_map, config)
    logger.info(f"World width confirmed: {ww}px")
    progress("base_map", 55)

    # ── Accumulate from cached PNGs ──
    progress("detect", 60)
    from pipeline.aggregate import accumulate, seam_roll
    presence = accumulate(screenshots_dir, segments,
                          base_map, config)
    progress("detect", 70)

    # ── Seam roll ──
    progress("seam_roll", 75)
    rolled_presence, rolled_bg, roll_offset = seam_roll(
        presence, base_map, config
    )

    # ── Render hero ──
    progress("render", 80)
    from pipeline.render import build_lut, render_hero
    lut = build_lut(config)
    hero = render_hero(rolled_presence, rolled_bg, config,
                       lut=lut)

    # ── Hourly snapshots ──
    progress("render", 85)
    hourly = _build_hourly_snapshots(
        segments, screenshots_dir, base_map, config
    )

    # ── Compose poster ──
    progress("compose", 90)
    from pipeline.poster import compose_poster, save_poster
    poster = compose_poster(
        hero, hourly, segments, rolled_presence, config
    )

    # ── Save poster ──
    progress("save", 93)
    poster_path = output_dir / "poster.png"
    save_poster(poster, poster_path)

    # ── ZIP screenshots ──
    progress("zip", 97)
    zip_path = output_dir / "screenshots.zip"
    with zipfile.ZipFile(zip_path, "w",
                          zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(screenshots_dir.glob("*.png")):
            zf.write(f, f.name)

    peak = int(rolled_presence.max())
    total = int(rolled_presence.sum())
    progress("done", 100)
    logger.info(
        f"Pipeline complete: poster={poster_path}, "
        f"max_persistence={peak}, "
        f"total_detection_pixels={total}"
    )
    return {
        "poster_path": str(poster_path),
        "zip_path": str(zip_path),
        "presence_max": peak,
        "total_detection_pixels": total,
    }


def _extract_frames(mp4_path, segments, screenshots_dir,
                    config) -> None:
    """Pass 2: sequential decode, write only representative
    frames. Sets seg['file'] on each segment in place."""
    plan = {}
    for seg in segments:
        plan[seg["rep_frame"]] = seg

    cap = cv2.VideoCapture(str(mp4_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open: {mp4_path}")

    max_idx = max(plan.keys()) if plan else 0
    idx = 0
    saved = 0
    while idx <= max_idx:
        ret, frame = cap.read()
        if not ret:
            break
        if idx in plan:
            seg = plan[idx]
            ts = seg["utc_start"].strftime("%H%M")
            te = seg["utc_end"].strftime("%H%M")
            step = seg["window_num"] + 1
            fname = (f"step_{step:03d}_"
                     f"{ts}-{te}Z.png")
            fpath = screenshots_dir / fname
            cv2.imwrite(str(fpath), frame)
            seg["file"] = fname
            saved += 1
        idx += 1
    cap.release()
    logger.info(f"Extracted {saved} frames to {screenshots_dir}")


def _build_hourly_snapshots(segments, screenshots_dir,
                             base_map, config) -> list[dict]:
    """Build hourly snapshot list from cached PNGs."""
    from pipeline.detect import detect_frame
    cadence = config.get("hourly", {}).get("cadence_steps", 6)
    WW = int(config["world"]["tile_width"])
    world_bg = base_map[:, WW:2*WW]
    results = []
    for seg in segments:
        if seg["window_num"] % cadence != 0:
            continue
        fname = seg.get("file")
        if not fname:
            continue
        fpath = screenshots_dir / fname
        frame = cv2.imread(str(fpath))
        if frame is None:
            continue
        detected = detect_frame(frame, base_map, config)
        snapshot = world_bg.copy()
        snapshot[detected] = [255, 255, 0]
        results.append({"segment": seg, "image": snapshot})
    logger.info(f"Built {len(results)} hourly snapshots")
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="GNSS Spoofing Aggregator"
    )
    parser.add_argument("mp4_path")
    parser.add_argument("output_dir")
    args = parser.parse_args()

    def cb(stage, pct):
        print(f"\r[{pct:3d}%] {stage:<20}",
              end="", flush=True)

    result = run(args.mp4_path, args.output_dir,
                 progress_callback=cb)
    print()
    print(f"Poster:      {result['poster_path']}")
    print(f"Screenshots: {result['zip_path']}")
    print(f"Max persistence:        {result['presence_max']}")
    print(f"Total detection pixels: "
          f"{result['total_detection_pixels']:,}")


if __name__ == "__main__":
    main()
