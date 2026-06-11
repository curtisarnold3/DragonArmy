"""World map calibration: NCC autocorrelation and temporal median base map."""

import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)


def find_world_width(frame: np.ndarray) -> int:
    """Find horizontal tile-repeat period via NCC autocorrelation."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h = gray.shape[0]
    strip = gray[h//3 : 2*h//3, :]
    row = strip.mean(axis=0).astype(np.float64)
    corr = np.correlate(row, row, mode='full')
    center = len(row) - 1
    search = corr[center + len(row)*3//8 : center + len(row)]
    peak_offset = int(np.argmax(search))
    width = peak_offset + len(row)*3//8
    logger.info(f"World width: {width}px")
    return width


def build_base_map(mp4_path, config: dict) -> np.ndarray:
    """Build clean background via per-pixel temporal median with logo paint-out."""
    from pipeline.probe import probe
    meta = probe(mp4_path)
    nb_frames = meta["nb_frames"]

    n = config.get("base_map", {}).get("sample_frames", 45)
    indices = sorted(set(int(i) for i in np.linspace(0, nb_frames - 1, n)))

    from pipeline.grabber import grab_all_frames_sampled
    frames_dict = grab_all_frames_sampled(mp4_path, indices, width=meta["width"], height=meta["height"])
    frame_list = [frames_dict[i] for i in indices if i in frames_dict]
    frames = np.stack(frame_list)
    base = np.median(frames, axis=0).astype(np.uint8)

    logo = config.get("masks", {}).get("logo")
    if logo is None:
        logger.warning("No logo mask in config; skipping paint-out")
    else:
        x0, x1 = logo["x"]
        y0, y1 = logo["y"]
        by0 = max(0, y0 - 10)
        by1 = min(base.shape[0], y1 + 10)
        bx0 = max(0, x0 - 10)
        bx1 = min(base.shape[1], x1 + 10)
        border_region = base[by0:by1, bx0:bx1].copy()
        border_region[y0-by0:y1-by0, x0-bx0:x1-bx0] = 0
        mask = border_region.any(axis=2)
        fill_color = np.median(border_region[mask].reshape(-1, 3), axis=0).astype(np.uint8)
        base[y0:y1, x0:x1] = fill_color

    logger.info(f"Base map built from {len(indices)} frames; logo box painted")
    return base
