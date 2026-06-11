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

    result = find_world_width(frame)
    assert abs(result - 300) <= 20


def test_find_world_width_returns_int():
    """Find world width returns exact int type."""
    tile = np.zeros((100, 300, 3), dtype=np.uint8)
    for x in range(300):
        tile[:, x, :] = int(128 + 127 * np.sin(x * 2 * np.pi / 300))
    frame = np.concatenate([tile, tile], axis=1)

    assert isinstance(find_world_width(frame), int)


def test_build_base_map_shape_and_dtype():
    """Build base map returns correct shape and dtype."""
    fake_frame = np.zeros((100, 200, 3), dtype=np.uint8)

    fake_meta = {"nb_frames": 10, "width": 200, "height": 100}

    cfg = {"base_map": {"sample_frames": 5}, "masks": {}}

    with patch("pipeline.probe.probe", return_value=fake_meta):
        with patch("pipeline.grabber.grab_all_frames_sampled", return_value={i: fake_frame for i in range(5)}):
            result = build_base_map("dummy.mp4", cfg)

    assert result.shape == (100, 200, 3)
    assert result.dtype == np.uint8


def test_build_base_map_logo_paintout():
    """Build base map paints out logo region."""
    # Create frame with logo area having different value (200) than surroundings (100)
    fake_frame = np.ones((100, 200, 3), dtype=np.uint8) * 100
    fake_frame[50:100, 150:200] = 200  # Logo area is brighter

    fake_meta = {"nb_frames": 10, "width": 200, "height": 100}

    cfg = {
        "base_map": {"sample_frames": 5},
        "masks": {"logo": {"x": [150, 200], "y": [50, 100]}}
    }

    with patch("pipeline.probe.probe", return_value=fake_meta):
        with patch("pipeline.grabber.grab_all_frames_sampled", return_value={i: fake_frame.copy() for i in range(5)}):
            result = build_base_map("dummy.mp4", cfg)

    # Logo region should be painted with border median (close to 100, not 200)
    logo_region = result[50:100, 150:200]
    logo_mean = logo_region.mean()
    assert logo_mean < 150, f"Logo region not painted: mean={logo_mean}, expected <150"

    # Non-logo region should remain close to 100
    non_logo = result[0:50, 0:150]
    assert np.all(np.abs(non_logo.astype(int) - 100) < 5)
