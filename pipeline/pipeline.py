"""CLI orchestrator for GNSS Spoofing Aggregator pipeline."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run(mp4_path, output_dir, progress_callback=None) -> dict:
    """Run the full pipeline end to end.

    Args:
        mp4_path: path to input MP4
        output_dir: output directory for poster and screenshots
        progress_callback: optional callback(stage_name: str, percent: int)

    Returns:
        dict with poster_path, zip_path, presence_max, total_detection_pixels
    """
    import yaml
    import zipfile
    import numpy as np
    import cv2

    mp4_path = Path(mp4_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    screenshots_dir = output_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    def progress(stage, pct):
        if progress_callback:
            progress_callback(stage, pct)
        logger.info(f"[{pct:3d}%] {stage}")

    with open(Path(__file__).parent / "config.yaml") as f:
        config = yaml.safe_load(f)

    # Step 1: Probe
    progress("probe", 5)
    from pipeline.probe import probe
    meta = probe(mp4_path)

    # Step 2: Find world width
    progress("calibrate", 10)
    from pipeline.grabber import grab_frame
    from pipeline.calibrate import find_world_width
    mid = grab_frame(mp4_path, meta["nb_frames"] // 2, width=meta["width"], height=meta["height"])
    world_width = find_world_width(mid)

    # Step 3: Compute title diffs
    progress("segment", 20)
    from pipeline.segment import compute_title_diffs, find_segment_boundaries, assign_times
    diffs = compute_title_diffs(mp4_path, config)

    # Step 4: Find boundaries + assign times
    progress("segment", 25)
    threshold = config["segmentation"]["transition_threshold"]
    boundaries = find_segment_boundaries(diffs, threshold)
    segments = assign_times(boundaries, config)
    logger.info(f"Found {len(segments)} segments")

    # Step 5: Prefetch all frames in one pass
    progress("prefetch", 30)
    from pipeline.grabber import grab_all_frames_sampled

    # Base map indices: 45 evenly spaced frames
    n_samples = config.get("base_map", {}).get("sample_frames", 45)
    base_indices = sorted(set(int(i) for i in np.linspace(0, meta["nb_frames"]-1, n_samples)))

    # Representative frame indices for all segments
    rep_pos = config["segmentation"]["representative_position"]
    rep_indices = []
    for seg in segments:
        if seg["end_frame"] is None:
            continue
        idx = int(seg["start_frame"] + (seg["end_frame"] - seg["start_frame"]) * rep_pos)
        rep_indices.append(idx)

    # Combine and fetch once
    all_indices = sorted(set(base_indices + rep_indices))
    prefetched_frames = grab_all_frames_sampled(mp4_path, all_indices, width=meta["width"], height=meta["height"])
    logger.info(f"Prefetched {len(all_indices)} frames in one pass")

    # Step 6: Build base map
    progress("base_map", 60)
    from pipeline.calibrate import build_base_map
    base_map = build_base_map(mp4_path, config, frames_dict=prefetched_frames)

    # Step 6: Save screenshots
    progress("screenshots", 40)
    rep_pos = config["segmentation"]["representative_position"]
    for i, seg in enumerate(segments):
        if seg["end_frame"] is None:
            continue
        idx = int(seg["start_frame"] + (seg["end_frame"] - seg["start_frame"]) * rep_pos)
        frame = grab_frame(mp4_path, idx, width=meta["width"], height=meta["height"])
        ts = seg["utc_start"].strftime("%H%M")
        te = seg["utc_end"].strftime("%H%M")
        fname = f"step_{seg['window_num']:03d}_{ts}-{te}z.png"
        cv2.imwrite(str(screenshots_dir / fname), frame)
        pct = 40 + int((i / len(segments)) * 10)
        progress("screenshots", pct)

    # Step 7: Accumulate
    progress("detect", 70)
    from pipeline.aggregate import accumulate, seam_roll
    presence = accumulate(mp4_path, segments, base_map, config, frames_dict=prefetched_frames)

    # Step 8: Seam roll
    progress("seam_roll", 75)
    rolled_presence, rolled_bg, roll_offset = seam_roll(presence, base_map, config)

    # Step 9: Render hero
    progress("render", 80)
    from pipeline.render import build_lut, render_hero
    lut = build_lut(config)
    hero = render_hero(rolled_presence, rolled_bg, config, lut=lut)

    # Step 10: Render hourly snapshots
    progress("render", 85)
    from pipeline.render import render_hourly_snapshots
    hourly = render_hourly_snapshots(mp4_path, segments, base_map, config)

    # Step 11: Compose poster
    progress("compose", 90)
    from pipeline.poster import compose_poster, save_poster
    poster = compose_poster(hero, hourly, segments, rolled_presence, config)

    # Step 12: Save poster
    progress("save", 93)
    poster_path = output_dir / "poster.png"
    save_poster(poster, poster_path)

    # Step 13: Save screenshots ZIP
    progress("zip", 97)
    zip_path = output_dir / "screenshots.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(screenshots_dir.glob("*.png")):
            zf.write(f, f.name)

    # Step 14: Done
    peak = int(rolled_presence.max())
    total = int(rolled_presence.sum())
    progress("done", 100)
    logger.info(f"Pipeline complete: poster={poster_path}, zip={zip_path}, max_persistence={peak}, total_detection_pixels={total}")

    return {
        "poster_path": str(poster_path),
        "zip_path": str(zip_path),
        "presence_max": peak,
        "total_detection_pixels": total,
    }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="GNSS Spoofing Aggregator — produce poster + screenshots from MP4")
    parser.add_argument("mp4_path", help="Input MP4 file")
    parser.add_argument("output_dir", help="Output directory")
    args = parser.parse_args()

    def cb(stage, pct):
        print(f"\r[{pct:3d}%] {stage:<20}", end="", flush=True)

    result = run(args.mp4_path, args.output_dir, progress_callback=cb)
    print()
    print(f"Poster:      {result['poster_path']}")
    print(f"Screenshots: {result['zip_path']}")
    print(f"Max persistence:        {result['presence_max']}")
    print(f"Total detection pixels: {result['total_detection_pixels']:,}")


if __name__ == "__main__":
    main()
