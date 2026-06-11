"""Tests for pipeline.aggregate"""

import numpy as np
import pytest
from unittest.mock import patch

from pipeline.aggregate import accumulate, seam_roll


@pytest.fixture
def cfg():
    return {
        "detection": {
            "luminance_weights": [0.114, 0.587, 0.299],
            "threshold": 14.0,
        },
        "masks": {
            "title": {"x": [2, 4], "y": [0, 1]},
            "logo":  {"x": [6, 8], "y": [0, 1]},
        },
        "segmentation": {"representative_position": 0.55},
        "seam_roll": {"smoothing_kernel": 3},
    }


def test_accumulate_shape_and_dtype(cfg):
    """Accumulate returns correct shape and dtype."""
    base = np.zeros((10, 20, 3), dtype=np.uint8)
    fake_frame = np.zeros((10, 20, 3), dtype=np.uint8)
    segments = [{"start_frame": 0, "end_frame": 10}]

    fake_meta = {"width": 20, "height": 10}

    with patch("pipeline.probe.probe", return_value=fake_meta):
        with patch("pipeline.grabber.grab_frames_batch", return_value={5: fake_frame}):
            result = accumulate("dummy.mp4", segments, base, cfg)

    assert result.shape == (10, 10)
    assert result.dtype == np.uint16


def test_accumulate_counts_detections(cfg):
    """Accumulate counts detections across segments."""
    base = np.zeros((10, 20, 3), dtype=np.uint8)
    bright = np.zeros((10, 20, 3), dtype=np.uint8)
    bright[5, 15, 2] = 200
    segments = [
        {"start_frame": 0, "end_frame": 10},
        {"start_frame": 10, "end_frame": 20},
    ]

    fake_meta = {"width": 20, "height": 10}

    with patch("pipeline.probe.probe", return_value=fake_meta):
        with patch("pipeline.grabber.grab_frames_batch", return_value={5: bright, 15: bright}):
            result = accumulate("dummy.mp4", segments, base, cfg)

    assert result[5, 5] == 2


def test_seam_roll_output_shapes(cfg):
    """Seam roll returns correct output shapes."""
    presence = np.zeros((10, 10), dtype=np.uint16)
    presence[:, 3] = 5
    base = np.zeros((10, 20, 3), dtype=np.uint8)

    rolled_p, rolled_bg, roll = seam_roll(presence, base, cfg)

    assert rolled_p.shape == presence.shape
    assert rolled_bg.shape == (10, 10, 3)
    assert isinstance(roll, int)
