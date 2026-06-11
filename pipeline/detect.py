"""Per-frame GNSS spoofing detection via luminance diff, mask, and fold."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def detect_frame(frame, base_map, config):
    """Isolate detections using proven working logic."""
    WW = int(config["world"]["tile_width"])
    H = base_map.shape[0]
    Wfull = base_map.shape[1]
    thr = config["detection"]["threshold"]

    base = base_map.astype(np.int16)
    diff = frame.astype(np.int16) - base
    bl = (0.114*diff[:,:,0] +
          0.587*diff[:,:,1] +
          0.299*diff[:,:,2])
    binc = np.clip(bl, 0, None).astype(np.float32)

    # Mask overlays
    title = config["masks"]["title"]
    logo = config["masks"]["logo"]
    binc[title["y"][0]:title["y"][1],
         title["x"][0]:title["x"][1]] = 0
    binc[logo["y"][0]:logo["y"][1],
         logo["x"][0]:logo["x"][1]] = 0

    # Fold two world copies via per-pixel max
    A = binc[:, WW:2*WW]
    B = binc[:, 0:WW]
    wbinc = np.maximum(A, B)

    return wbinc > thr
