"""Compose final poster with banner, legend, grid, and footer."""

import logging
import numpy as np
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)


def compose_poster(hero: np.ndarray, hourly_snapshots: list[dict], segments: list[dict], presence: np.ndarray, config: dict) -> np.ndarray:
    """Compose the full poster with banner, hero map, legend, snapshot grid, and footer.

    Args:
        hero: (H, W, 3) uint8 BGR hero map image
        hourly_snapshots: list of {segment, image} dicts
        segments: list of segment dicts with utc_start, utc_end
        presence: (H, WW) uint16 per-pixel window count
        config: loaded config.yaml dict

    Returns:
        uint8 BGR poster image
    """
    # Step 1: Crop hero to active latitudes
    crop = config.get("poster", {}).get("crop", {})
    y_top = crop.get("y_top", 150)
    y_bottom = crop.get("y_bottom", 1070)
    hero_cropped = hero[y_top:y_bottom, :]

    # Scale to reference width for consistent poster dimensions
    TARGET_W = 1197
    if hero_cropped.shape[1] != TARGET_W:
        scale = TARGET_W / hero_cropped.shape[1]
        new_h = int(hero_cropped.shape[0] * scale)
        hero_cropped = cv2.resize(
            hero_cropped,
            (TARGET_W, new_h),
            interpolation=cv2.INTER_LANCZOS4
        )

    # Step 2: Set poster dimensions
    hero_h, hero_w = hero_cropped.shape[:2]
    BANNER_H = 80
    LEGEND_H = 120
    FOOTER_H = 40
    GRID_ROWS = 4
    GRID_COLS = 6
    snap_w = hero_w // GRID_COLS
    snap_h = snap_w * hero_cropped.shape[0] // hero_w
    GRID_H = snap_h * GRID_ROWS
    total_h = BANNER_H + hero_h + LEGEND_H + GRID_H + FOOTER_H
    poster = np.zeros((total_h, hero_w, 3), dtype=np.uint8)
    poster[:] = [15, 15, 20]  # near-black background (BGR)

    # Step 3: Draw banner
    title = "GNSS SPOOFING — AGGREGATE DENSITY"
    cv2.putText(poster, title, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    if segments:
        date_str = segments[0]["utc_start"].strftime("%Y-%m-%d")
        first_t = segments[0]["utc_start"].strftime("%H:%MZ")
        last_t = segments[-1]["utc_end"].strftime("%H:%MZ")
        subtitle = f"{date_str}  |  {first_t} - {last_t}"
        cv2.putText(poster, subtitle, (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    # Step 4: Place hero map
    y_start = BANNER_H
    poster[y_start:y_start + hero_h, :] = hero_cropped

    # Step 5: Draw legend with colormap bar
    y_start = BANNER_H + hero_h
    from pipeline.render import build_lut
    lut = build_lut(config)
    indices = np.linspace(0, 255, hero_w).astype(np.uint8)
    bar = lut[indices].reshape(1, hero_w, 3)
    bar = np.repeat(bar, 20, axis=0)
    poster[y_start + 10:y_start + 30, :] = bar

    # Draw legend labels
    cv2.putText(poster, "1 window", (10, y_start + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(poster, "57 windows (~9.5h)", (hero_w - 180, y_start + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(poster, "~29 windows", (hero_w // 2 - 60, y_start + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Step 6: Draw stats block
    peak = int(presence.max())
    total = int(presence.sum())
    stats_text = f"Max persistence: {peak} windows  |  Total detection pixels: {total:,}"
    cv2.putText(poster, stats_text, (20, y_start + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    # Step 7: Place hourly snapshot grid
    y_start = BANNER_H + hero_h + LEGEND_H
    for i, snap_dict in enumerate(hourly_snapshots[:GRID_ROWS * GRID_COLS]):
        snapshot = snap_dict["image"]
        seg = snap_dict["segment"]

        # Crop and resize snapshot
        snapshot_cropped = snapshot[y_top:y_bottom, :]
        resized = cv2.resize(snapshot_cropped, (snap_w, snap_h), interpolation=cv2.INTER_AREA)

        # Compute grid position
        row = i // GRID_COLS
        col = i % GRID_COLS
        y = y_start + row * snap_h
        x = col * snap_w

        poster[y:y + snap_h, x:x + snap_w] = resized

        # Draw UTC label
        label = seg["utc_start"].strftime("%H:%MZ")
        cv2.putText(poster, label, (x + 5, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Step 8: Draw footer
    y_start = BANNER_H + hero_h + LEGEND_H + GRID_H
    footer_text = ("Method: temporal median base map | luminance threshold | per-pixel max fold | "
                   "Source: Slingshot GNSS SPOOFING (Standard)")
    cv2.putText(poster, footer_text, (20, y_start + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

    # Step 9: Log and return
    logger.info(f"Poster composed: {poster.shape[1]}x{poster.shape[0]}px")
    return poster


def save_poster(poster: np.ndarray, output_path) -> None:
    """Save the poster PNG to disk.

    Args:
        poster: uint8 BGR image
        output_path: destination file path
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), poster)
    logger.info(f"Poster saved: {out}")
