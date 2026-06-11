"""Accumulate detections across windows and roll to emptiest seam."""

import logging

import numpy as np
from scipy.ndimage import uniform_filter1d

logger = logging.getLogger(__name__)


def accumulate(mp4_path, segments: list[dict], base_map: np.ndarray, config: dict) -> np.ndarray:
    """Return uint16 (H, WW) array counting detections per pixel across all windows."""
    from pipeline.probe import probe
    meta = probe(mp4_path)

    H = base_map.shape[0]
    WW = base_map.shape[1] // 2
    presence = np.zeros((H, WW), dtype=np.uint16)

    from pipeline.detect import detect_frame

    rep_pos = config.get("segmentation", {}).get("representative_position", 0.55)

    # Phase 1: Collect representative frame indices
    rep_indices = []
    for seg in segments:
        start = seg["start_frame"]
        end = seg["end_frame"]
        if end is None:
            continue
        idx = int(start + (end - start) * rep_pos)
        rep_indices.append((seg, idx))

    # Phase 2: Batch extract all frames
    from pipeline.grabber import grab_all_frames_sampled
    all_idx = [idx for _, idx in rep_indices]
    frames_dict = grab_all_frames_sampled(mp4_path, all_idx, width=meta["width"], height=meta["height"])

    # Phase 3: Accumulate detections
    for seg, idx in rep_indices:
        if idx not in frames_dict:
            continue
        frame = frames_dict[idx]
        detected = detect_frame(frame, base_map, config)
        presence += detected.astype(np.uint16)

    total = int(presence.sum())
    peak = int(presence.max())
    logger.info(f"Accumulation complete: max_persistence={peak}, total_detection_pixels={total}")
    return presence


def seam_roll(presence: np.ndarray, base_map: np.ndarray, config: dict) -> tuple[np.ndarray, np.ndarray, int]:
    """Roll presence and base_map so seam sits in emptiest column."""
    WW = presence.shape[1]
    world_bg = base_map[:, WW:2*WW]

    col_energy = presence.sum(axis=0).astype(np.float64)

    kernel_size = config.get("seam_roll", {}).get("smoothing_kernel", 60)
    smoothed = uniform_filter1d(col_energy, size=kernel_size, mode='wrap')

    seam_col = int(np.argmin(smoothed))
    roll = -seam_col
    logger.info(f"Seam roll: seam_col={seam_col}, roll={roll}")

    rolled_presence = np.roll(presence, roll, axis=1)
    rolled_bg = np.roll(world_bg, roll, axis=1)

    return rolled_presence, rolled_bg, roll
