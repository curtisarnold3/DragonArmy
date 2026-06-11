"""Tests for pipeline.calibrate"""

import numpy as np
import pytest
from unittest.mock import patch

from pipeline.calibrate import find_world_width, build_base_map


def test_find_world_width_on_tiled_frame():
    """Find world width detects horizontal tile repeat period."""
    # Create tile with horizontal gradient for strong correlation structure
    tile = np.zeros((100, 300, 3), dtype=np.uint8)
    for x in range(300):
        tile[:, x, :] = int(128 + 127 * np.sin(x * 2 * np.pi / 300))
    frame = np.concatenate([tile, tile], axis=1)  # shape: (100, 600, 3)

    config = {"world": {"tile_width": "auto"}}
    result = find_world_width(frame, config)
    assert abs(result - 300) <= 20


def test_find_world_width_returns_int():
    """Find world width returns exact int type."""
    tile = np.zeros((100, 300, 3), dtype=np.uint8)
    for x in range(300):
        tile[:, x, :] = int(128 + 127 * np.sin(x * 2 * np.pi / 300))
    frame = np.concatenate([tile, tile], axis=1)

    config = {"world": {"tile_width": "auto"}}
    assert isinstance(find_world_width(frame, config), int)


def test_build_base_map_shape_and_dtype(tmp_path):
    """Build base map returns correct shape and dtype."""
    import cv2
    fake_frame = np.zeros((100, 200, 3), dtype=np.uint8)
    for i in range(5):
        cv2.imwrite(str(tmp_path / f"step_{i:03d}_0000-0130z.png"), fake_frame)

    cfg = {"base_map": {"sample_frames": 5}, "masks": {}}
    result = build_base_map(tmp_path, cfg)

    assert result.shape == (100, 200, 3)
    assert result.dtype == np.uint8


def test_build_base_map_logo_paintout(tmp_path):
    """Build base map paints out logo region."""
    import cv2
    # Create frame with logo area having different value (200) than surroundings (100)
    fake_frame = np.ones((100, 200, 3), dtype=np.uint8) * 100
    fake_frame[50:100, 150:200] = 200  # Logo area is brighter

    for i in range(5):
        cv2.imwrite(str(tmp_path / f"step_{i:03d}_0000-0130z.png"), fake_frame.copy())

    cfg = {
        "base_map": {"sample_frames": 5},
        "masks": {"logo": {"x": [150, 200], "y": [50, 100]}}
    }
    result = build_base_map(tmp_path, cfg)

    # Logo region should be painted with border median (close to 100, not 200)
    logo_region = result[50:100, 150:200]
    logo_mean = logo_region.mean()
    assert logo_mean < 150, f"Logo region not painted: mean={logo_mean}, expected <150"

    # Non-logo region should remain close to 100
    non_logo = result[0:50, 0:150]
    assert np.all(np.abs(non_logo.astype(int) - 100) < 5)
