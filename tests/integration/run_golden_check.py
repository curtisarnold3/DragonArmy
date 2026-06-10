"""Temporary script to capture golden-master values from the reference MP4.
Run inside the Docker container: python3 tests/integration/run_golden_check.py
Delete after golden values are confirmed and locked into a proper test.
"""
import sys
import yaml
import numpy as np
import logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from pipeline.probe import probe
from pipeline.calibrate import find_world_width, build_base_map
from pipeline.segment import (
    compute_title_diffs, find_segment_boundaries, assign_times
)
from pipeline.aggregate import accumulate
from pipeline.grabber import grab_frame

MP4 = "tests/golden/deep-haerts-video_2026-06-10T15_52_21.682Z.mp4"

with open("pipeline/config.yaml") as f:
    config = yaml.safe_load(f)

print("=== PROBE ===")
meta = probe(MP4)
print(f"width={meta['width']} height={meta['height']} "
      f"fps={meta['fps']} nb_frames={meta['nb_frames']}")

print("=== CALIBRATE ===")
mid = grab_frame(MP4, meta["nb_frames"] // 2)
ww = find_world_width(mid)
print(f"world_width={ww}")
base = build_base_map(MP4, ww, config)
print(f"base_map shape={base.shape}")

print("=== SEGMENT ===")
diffs = compute_title_diffs(MP4, config)
thresh = config["segmentation"]["transition_threshold"]
bounds = find_segment_boundaries(diffs, thresh)
segs = assign_times(bounds, config)
print(f"num_segments={len(segs)}")
if segs:
    print(f"first_window={segs[0]['utc_start'].strftime('%H:%MZ')}")
    print(f"last_window={segs[-1]['utc_start'].strftime('%H:%MZ')}")

print("=== ACCUMULATE ===")
presence = accumulate(MP4, segs, base, config)
peak = int(presence.max())
total = int(presence.sum())
print(f"max_persistence={peak}")
print(f"total_detection_pixels={total}")
print(f"peak_match={'OK' if peak == 57 else 'MISMATCH (expected 57)'}")
print(f"total_match={'OK' if abs(total - 29538) < 500 else 'MISMATCH (expected ~29538)'}")
