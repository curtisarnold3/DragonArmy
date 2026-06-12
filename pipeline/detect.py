"""Per-frame GNSS spoofing detection via luminance diff, mask, and fold."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def detect_frame(frame, base_map, config, is_tiled=True):
    """Isolate detections using proven working logic.
    Supports any resolution via normalized mask coordinates.

    Args:
        frame: Current frame (H × W × 3)
        base_map: Base map (H × W × 3)
        config: Pipeline config
        is_tiled: If True, fold two world copies; if False, single copy

    Returns:
        np.ndarray: Boolean mask (H × W) where True = detection
    """
    WW = int(config.get("world", {}).get("tile_width",
         frame.shape[1] // 2))
    H = base_map.shape[0]
    Wfull = base_map.shape[1]
    thr = config["detection"]["threshold"]

    base = base_map.astype(np.int16)
    diff = frame.astype(np.int16) - base
    bl = (0.114*diff[:,:,0] +
          0.587*diff[:,:,1] +
          0.299*diff[:,:,2])
    binc = np.clip(bl, 0, None).astype(np.float32)

    # Mask overlays - compute absolute coords from normalized values
    frame_h, frame_w = frame.shape[:2]
    title = config["masks"]["title"]
    logo = config["masks"]["logo"]
    tx0 = int(title["x_norm"][0] * frame_w)
    tx1 = int(title["x_norm"][1] * frame_w)
    ty0 = int(title["y_norm"][0] * frame_h)
    ty1 = int(title["y_norm"][1] * frame_h)
    lx0 = int(logo["x_norm"][0] * frame_w)
    lx1 = int(logo["x_norm"][1] * frame_w)
    ly0 = int(logo["y_norm"][0] * frame_h)
    ly1 = int(logo["y_norm"][1] * frame_h)

    binc[ty0:ty1, tx0:tx1] = 0
    binc[ly0:ly1, lx0:lx1] = 0

    # For single-copy layouts, skip fold
    if not is_tiled:
        return binc > thr

    # Fold two world copies via per-pixel max
    A = binc[:, WW:2*WW]
    B = binc[:, 0:WW]
    wbinc = np.maximum(A, B)

    return wbinc > thr

