"""Accumulate detections across windows and roll to emptiest seam."""

import logging
import numpy as np
import cv2
from pathlib import Path
from scipy.ndimage import uniform_filter1d

logger = logging.getLogger(__name__)


def accumulate(screenshots_dir, segments, base_map, config, is_tiled=True):
    """Accumulate presence using proven working logic.

    Args:
        screenshots_dir: Directory containing cached PNGs
        segments: List of segment dicts
        base_map: Temporal median base map
        config: Pipeline config
        is_tiled: If True, fold two world copies; if False, single copy

    Returns:
        np.ndarray: Presence array (H × W), dtype uint16
    """
    from pipeline.detect import detect_frame
    from pathlib import Path

    WW = int(config["world"]["tile_width"])
    H = base_map.shape[0]

    # For single-copy layouts, presence array is full frame width
    if not is_tiled:
        W = base_map.shape[1]
        presence = np.zeros((H, W), dtype=np.int32)
    else:
        presence = np.zeros((H, WW), dtype=np.int32)

    screenshots_dir = Path(screenshots_dir)

    for seg in segments:
        fname = seg.get("file")
        if fname is None:
            continue
        fpath = screenshots_dir / fname
        if not fpath.exists():
            logger.warning(f"Missing: {fpath}")
            continue
        fr = cv2.imread(str(fpath))
        if fr is None:
            continue
        mask = detect_frame(fr, base_map, config, is_tiled=is_tiled)
        presence += mask.astype(np.int32)

    total = int((presence > 0).sum())
    peak = int(presence.max())
    logger.info(
        f"Accumulation complete: "
        f"max_persistence={peak}, "
        f"total_detection_pixels={total}"
    )
    return presence.astype(np.uint16)


def seam_roll(
    presence: np.ndarray,
    base_map: np.ndarray,
    config: dict,
    is_tiled: bool = True,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Roll presence and background to put seam in empty ocean.

    Args:
        presence: Presence array (H × W)
        base_map: Base map image
        config: Pipeline config
        is_tiled: If True, extract world_bg from second tile; if False, use base_map as-is

    Returns:
        tuple[np.ndarray, np.ndarray, int]: (rolled_presence, rolled_bg, roll_offset)
    """
    # For single-copy layouts, skip rolling
    if not is_tiled:
        logger.info("Single-copy layout detected, skipping seam roll")
        return presence, base_map, 0

    WW = presence.shape[1]
    world_bg = base_map[:, WW:2*WW]

    col_energy = presence.sum(axis=0).astype(np.float64)
    kernel_size = config.get("seam_roll", {}).get(
        "smoothing_kernel", 60
    )
    smoothed = uniform_filter1d(
        col_energy, size=kernel_size, mode='wrap'
    )
    seam_col = int(np.argmin(smoothed))
    roll = -seam_col
    logger.info(f"Seam roll: seam_col={seam_col}, roll={roll}")

    rolled_presence = np.roll(presence, roll, axis=1)
    rolled_bg = np.roll(world_bg, roll, axis=1)
    return rolled_presence, rolled_bg, roll
