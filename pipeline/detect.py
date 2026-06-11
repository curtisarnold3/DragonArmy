"""Per-frame GNSS spoofing detection via luminance diff, mask, and fold."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def detect_frame(frame: np.ndarray, base_map: np.ndarray, config: dict) -> np.ndarray:
    """Return boolean (H, WW) array where True = detection."""
    # STEP 1: Compute luminance-weighted diff
    diff = frame.astype(np.int16) - base_map.astype(np.int16)
    luminance = (
        0.114 * diff[:, :, 0] +
        0.587 * diff[:, :, 1] +
        0.299 * diff[:, :, 2]
    )
    luminance = np.clip(luminance, 0, None).astype(np.float32)

    # STEP 2: Threshold positive luminance increases
    threshold = config["detection"]["threshold"]
    detected = luminance > threshold

    # STEP 3: Zero out title mask
    title = config["masks"]["title"]
    detected[title["y"][0]:title["y"][1], title["x"][0]:title["x"][1]] = False

    # STEP 4: Zero out logo mask
    logo = config["masks"]["logo"]
    detected[logo["y"][0]:logo["y"][1], logo["x"][0]:logo["x"][1]] = False

    # STEP 5: Fold two world tiles via per-pixel max
    WW = config.get("world", {}).get("tile_width", "auto")
    if WW == "auto":
        WW = frame.shape[1] // 2
    WW = int(WW)
    tile_a = detected[:, WW:2*WW]
    tile_b = detected[:, :WW]
    folded = np.logical_or(tile_a, tile_b)

    return folded
