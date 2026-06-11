"""Render hero map and hourly snapshots with custom colormap."""

import logging
import numpy as np
import cv2

logger = logging.getLogger(__name__)


def build_lut(config: dict) -> np.ndarray:
    """Build a 256×3 uint8 lookup table from colormap stops in config.

    Returns array of shape (256, 3) in BGR order (OpenCV convention).
    """
    stops = config["render"]["colormap"]
    lut = np.zeros((256, 3), dtype=np.uint8)

    for i in range(256):
        t = i / 255.0

        # Find bracketing stops
        left_stop = stops[0]
        right_stop = stops[-1]
        for j in range(len(stops) - 1):
            if stops[j][0] <= t <= stops[j + 1][0]:
                left_stop = stops[j]
                right_stop = stops[j + 1]
                break

        # Interpolate
        left_t, left_rgb = left_stop
        right_t, right_rgb = right_stop

        if right_t == left_t:
            weight = 0.0
        else:
            weight = (t - left_t) / (right_t - left_t)

        r = int(left_rgb[0] * (1 - weight) + right_rgb[0] * weight)
        g = int(left_rgb[1] * (1 - weight) + right_rgb[1] * weight)
        b = int(left_rgb[2] * (1 - weight) + right_rgb[2] * weight)

        # Store as BGR
        lut[i] = [b, g, r]

    return lut


def render_hero(presence: np.ndarray, background: np.ndarray, config: dict, lut: np.ndarray = None) -> np.ndarray:
    """Produce the hero map — density colormap overlaid on background at overlay_alpha.

    Args:
        presence: (H, WW) uint16 — per-pixel window count
        background: (H, WW, 3) uint8 — the rolled base map tile
        config: loaded config.yaml dict
        lut: optional pre-built LUT; if None, call build_lut(config)

    Returns:
        uint8 BGR image (H, WW, 3)
    """
    if lut is None:
        lut = build_lut(config)

    # Normalize presence with gamma correction
    gamma = config["render"]["gamma"]
    max_val = presence.max()
    if max_val == 0:
        return background.copy()

    normalised = (presence / max_val).astype(np.float32)
    gamma_corrected = np.power(normalised, gamma)
    indices = (gamma_corrected * 255).astype(np.uint8)

    # Map through LUT
    colored = lut[indices]

    # Alpha mask - only pixels with detections get overlay
    alpha_mask = (presence > 0).astype(np.float32)
    overlay_alpha = config["render"]["overlay_alpha"]

    # Blend
    bg = background.astype(np.float32)
    fg = colored.astype(np.float32)
    alpha = (alpha_mask * overlay_alpha)[..., np.newaxis]
    blended = bg * (1 - alpha) + fg * alpha

    return blended.astype(np.uint8)


def render_hourly_snapshots(mp4_path, segments: list[dict], base_map: np.ndarray, config: dict, grab_frame_fn=None) -> list[dict]:
    """For each hourly segment, render a snapshot showing detections on clean background.

    Args:
        mp4_path: path to MP4 file
        segments: list of segment dicts with start_frame, end_frame, window_num
        base_map: (H, W, 3) uint8 base map (full width, not rolled)
        config: loaded config.yaml dict
        grab_frame_fn: optional frame grabber override

    Returns:
        list of dicts: {segment, image (np.ndarray BGR)}
    """
    if grab_frame_fn is None:
        from pipeline.grabber import grab_frame
        grab_frame_fn = grab_frame

    from pipeline.detect import detect_frame

    cadence = config.get("hourly", {}).get("cadence_steps", 6)
    rep_pos = config.get("segmentation", {}).get("representative_position", 0.55)

    results = []
    WW = base_map.shape[1] // 2
    world_bg = base_map[:, WW:2*WW].copy()

    for seg in segments:
        window_num = seg.get("window_num", 0)
        if window_num % cadence != 0:
            continue

        start = seg["start_frame"]
        end = seg["end_frame"]
        if end is None:
            continue

        idx = int(start + (end - start) * rep_pos)
        frame = grab_frame_fn(mp4_path, idx)

        detected = detect_frame(frame, base_map, config)

        # Highlight detections in cyan at 60% alpha
        highlight = world_bg.copy()
        highlight[detected] = [255, 255, 0]
        alpha = 0.6
        snapshot = cv2.addWeighted(world_bg, 1 - alpha, highlight, alpha, 0)

        results.append({
            "segment": seg,
            "image": snapshot,
        })

    logger.info(f"Rendered {len(results)} hourly snapshots")
    return results
