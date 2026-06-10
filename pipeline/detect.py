"""Per-frame GNSS spoofing detection via luminance diff, mask, and fold."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def detect_frame(frame: np.ndarray, base_map: np.ndarray, config: dict) -> np.ndarray:
    """Return boolean (H, WW) array where True = detection."""
    # STEP 1: Compute luminance-weighted diff
    weights = config["detection"]["luminance_weights"]
    diff = frame.astype(np.float32) - base_map.astype(np.float32)
    luminance = (
        diff[:, :, 0] * weights[0] +
        diff[:, :, 1] * weights[1] +
        diff[:, :, 2] * weights[2]
    )

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
    WW = frame.shape[1] // 2
    tile_a = detected[:, WW:]
    tile_b = detected[:, :WW]
    folded = np.logical_or(tile_a, tile_b)

    return folded
