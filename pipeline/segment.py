"""Video segmentation via title-region diff signal and UTC time labeling."""

import logging
import json
import numpy as np
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_title_diffs(mp4_path, config: dict) -> np.ndarray:
    """Sequential decode pass through entire video.
    Returns per-frame diff array of title region signatures.
    Uses cv2.VideoCapture for fast sequential read — no seeking.
    """
    mp4_path = str(mp4_path)
    tx1, ty1 = config["masks"]["title"]["x"][0], config["masks"]["title"]["y"][0]
    tx2, ty2 = config["masks"]["title"]["x"][1], config["masks"]["title"]["y"][1]

    cap = cv2.VideoCapture(mp4_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {mp4_path}")

    sigs = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        crop = frame[ty1:ty2, tx1:tx2]
        g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(g, (87, 6),
                           interpolation=cv2.INTER_AREA)
        sigs.append(small.flatten().astype(np.float32))
    cap.release()

    sigs = np.array(sigs)
    diffs = np.zeros(len(sigs))
    for i in range(1, len(sigs)):
        diffs[i] = np.mean(np.abs(sigs[i] - sigs[i-1]))

    logger.info(f"Title diffs computed: {len(diffs)} frames")
    return diffs


def find_segment_boundaries(
    diffs: np.ndarray,
    threshold: float
) -> list[tuple]:
    """Find clean segment boundaries using two-pass logic."""
    # Pass 1: coarse boundaries at threshold=8.0
    trans = [i for i in range(1, len(diffs)) if diffs[i] > 8.0]
    boundaries_1 = [0]
    for t in trans:
        if t - boundaries_1[-1] > 5:
            boundaries_1.append(t)
    boundaries_1.append(len(diffs))

    # Pass 2: refine using threshold parameter (0.5) on same diffs
    trans2 = [i for i in range(1, len(diffs)) if diffs[i] > threshold]
    merged = []
    for t in trans2:
        if not merged or t - merged[-1] > 8:
            merged.append(t)
        else:
            if diffs[t] > diffs[merged[-1]]:
                merged[-1] = t

    boundaries = [0] + merged + [len(diffs)]
    segs = []
    for b in range(len(boundaries) - 1):
        s, e = boundaries[b], boundaries[b+1]
        if e - s >= 6:
            segs.append((s, e))

    logger.info(f"Segments: {len(segs)} "
                f"(from {len(merged)} clean transitions)")
    return segs


def assign_times(
    segments: list[tuple],
    config: dict
) -> list[dict]:
    """Assign UTC times to segments. Segment 0 is intro,
    skipped. Segment k maps to window k-1."""
    from datetime import datetime, timezone, timedelta
    tm = config["time_model"]
    origin = datetime.fromisoformat(
        tm["origin_utc"].replace("Z", "+00:00")
    )
    step_min = tm["step_min"]
    lookback_min = tm["window_lookback_min"]
    intro_idx = tm.get("intro_segment", 0)
    rep_pos = config["segmentation"]["representative_position"]

    result = []
    for k, (s, e) in enumerate(segments):
        if k == intro_idx:
            continue
        window_num = k - 1
        utc_start = origin + timedelta(minutes=window_num * step_min)
        utc_end = utc_start + timedelta(minutes=lookback_min)
        mid = s + int((e - s) * rep_pos)
        result.append({
            "index": k,
            "window_num": window_num,
            "start_frame": s,
            "end_frame": e,
            "rep_frame": mid,
            "utc_start": utc_start,
            "utc_end": utc_end,
        })

    if result:
        logger.info(
            f"Segmentation: {len(result)} windows, "
            f"first={result[0]['utc_start'].strftime('%H:%MZ')}, "
            f"last={result[-1]['utc_start'].strftime('%H:%MZ')}"
        )
    return result
