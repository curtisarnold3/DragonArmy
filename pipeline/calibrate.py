"""World map calibration: NCC autocorrelation and temporal median base map."""

import logging
import numpy as np
import cv2
import scipy.signal as ss
from pathlib import Path

logger = logging.getLogger(__name__)


def find_world_width(base_map: np.ndarray,
                     config: dict) -> tuple[int, bool]:
    """Measure world tile width via autocorrelation of
    base map grayscale. Uses scipy.signal.find_peaks with
    distance=200 to find dominant lag. Falls back to
    config value if no peak found.

    Returns:
        tuple[int, bool]: (world_width, is_tiled)
        - world_width: detected tile width in pixels
        - is_tiled: True if two world copies detected, False for single copy
    """

    # Autocorrelation on equatorial band of base map
    g = cv2.cvtColor(base_map,
                     cv2.COLOR_BGR2GRAY).astype(np.float32)
    band = g[200:900, :].mean(axis=0)
    band = band - band.mean()
    ac = np.correlate(band, band, mode='full')
    ac = ac[ac.size // 2:]

    peaks, _ = ss.find_peaks(ac[200:], distance=200)
    peaks = peaks + 200

    if len(peaks) == 0:
        fallback = base_map.shape[1] // 2
        logger.warning(
            f"No autocorr peak found; using frame//2={fallback}, single-copy assumed"
        )
        return fallback, False

    order = np.argsort(ac[peaks])[::-1]
    top = peaks[order[0]]

    # Compute confidence: peak_value / mean_value
    peak_value = ac[top]
    mean_value = ac.mean()
    confidence = peak_value / mean_value if mean_value > 0 else 0.0
    is_tiled = confidence >= 2.0

    # Check config for pinned value
    tw = config.get("world", {}).get("tile_width", "auto")
    if tw != "auto":
        logger.info(f"World width from config: {tw}px, tiled: {is_tiled} (confidence: {confidence:.2f})")
        return int(tw), is_tiled

    logger.info(f"World width: {top}px, tiled: {is_tiled} (confidence: {confidence:.2f})")
    return int(top), is_tiled


def build_base_map(
    screenshots_dir,
    config: dict,
) -> np.ndarray:
    """Build temporal median base map from cached screenshot
    PNGs. Never re-opens the video. Fast."""
    screenshots_dir = Path(screenshots_dir)
    all_files = sorted([
        p for p in screenshots_dir.glob("step_*.png")
        if p.name.startswith("step_")
    ])
    files = [p for p in all_files]

    if not files:
        raise ValueError(
            f"No screenshot PNGs found in {screenshots_dir}. "
            "Run _extract_frames() before build_base_map()."
        )

    n = config.get("base_map", {}).get("sample_frames", 45)
    n = min(n, len(files))
    idx = np.linspace(0, len(files) - 1, n).astype(int)
    sampled = [str(files[i]) for i in idx]

    stack = np.stack(
        [cv2.imread(f) for f in sampled], axis=0
    ).astype(np.uint8)
    base = np.median(stack, axis=0).astype(np.uint8)
    del stack

    # Paint logo box with surrounding ocean color
    logo = config.get("masks", {}).get("logo")
    if logo:
        # Compute absolute coords from normalized values
        frame_h, frame_w = base.shape[:2]
        x0 = int(logo["x_norm"][0] * frame_w)
        x1 = int(logo["x_norm"][1] * frame_w)
        y0 = int(logo["y_norm"][0] * frame_h)
        y1 = int(logo["y_norm"][1] * frame_h)

        by0 = max(0, y0 - 10)
        by1 = min(base.shape[0], y1 + 10)
        bx0 = max(0, x0 - 10)
        bx1 = min(base.shape[1], x1 + 10)
        border = base[by0:by1, bx0:bx1].copy()
        border[y0-by0:y1-by0, x0-bx0:x1-bx0] = 0
        mask = border.any(axis=2)
        if mask.any():
            fill = np.median(
                border[mask].reshape(-1, 3), axis=0
            ).astype(np.uint8)
            base[y0:y1, x0:x1] = fill

    logger.info(
        f"Base map from {len(sampled)} screenshots; "
        f"logo box painted"
    )
    return base
