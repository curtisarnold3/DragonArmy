"""Video segmentation via title-region diff signal and UTC time labeling."""

import logging
from datetime import datetime, timedelta, timezone

import numpy as np

logger = logging.getLogger(__name__)


def compute_title_diffs(mp4_path, config: dict, grab_frame_fn=None) -> np.ndarray:
    """Compute frame-to-frame mean absolute diffs in title region."""
    if grab_frame_fn is None:
        from pipeline.grabber import grab_frame
        grab_frame_fn = grab_frame

    from pipeline.probe import probe
    meta = probe(mp4_path)
    nb_frames = meta["nb_frames"]

    title = config["masks"]["title"]
    x0, x1 = title["x"]
    y0, y1 = title["y"]

    diffs = []
    prev = None
    for i in range(nb_frames):
        frame = grab_frame_fn(mp4_path, i)
        region = frame[y0:y1, x0:x1]
        gray = region.mean(axis=2)
        if prev is not None:
            diffs.append(np.abs(gray.astype(float) - prev).mean())
        prev = gray
    return np.array(diffs, dtype=np.float64)


def find_segment_boundaries(diffs: np.ndarray, threshold: float) -> list[int]:
    """Return sorted list of frame indices where title transitions occur."""
    boundaries = [0]
    for i, d in enumerate(diffs):
        if d > threshold:
            boundaries.append(i + 1)
    return sorted(set(boundaries))


def assign_times(boundaries: list[int], config: dict) -> list[dict]:
    """Convert boundary frame indices to segment dicts with UTC times."""
    tm = config["time_model"]
    origin = datetime.fromisoformat(tm["origin_utc"].replace("Z", "+00:00"))
    step_min = tm["step_min"]
    lookback_min = tm["window_lookback_min"]
    intro_idx = tm.get("intro_segment", 0)

    segments = []
    for k in range(len(boundaries)):
        if k == intro_idx:
            continue
        window_num = k - (1 if intro_idx == 0 else 0)
        utc_start = origin + timedelta(minutes=window_num * step_min)
        utc_end = utc_start + timedelta(minutes=lookback_min)
        segments.append({
            "index": k,
            "window_num": window_num,
            "start_frame": boundaries[k],
            "end_frame": boundaries[k + 1] if k + 1 < len(boundaries) else None,
            "utc_start": utc_start,
            "utc_end": utc_end,
        })

    logger.info(f"Segmentation: {len(segments)} segments, first={segments[0]['utc_start'].strftime('%H:%MZ')}, last={segments[-1]['utc_start'].strftime('%H:%MZ')}")
    return segments
