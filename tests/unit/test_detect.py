"""Tests for pipeline.detect"""

import numpy as np
import pytest

from pipeline.detect import detect_frame


@pytest.fixture
def cfg():
    return {
        "detection": {
            "luminance_weights": [0.114, 0.587, 0.299],
            "threshold": 14.0,
        },
        "masks": {
            "title": {"x_norm": [0.1, 0.2], "y_norm": [0.0, 0.1]},  # 2/20=0.1, 4/20=0.2 for 20px wide frame
            "logo":  {"x_norm": [0.3, 0.4], "y_norm": [0.0, 0.1]},  # 6/20=0.3, 8/20=0.4
        },
        "world": {"tile_width": 10},
    }


@pytest.fixture
def blank():
    return np.zeros((10, 20, 3), dtype=np.uint8)


def test_detect_frame_shape(blank, cfg):
    """Detect frame returns correct shape and dtype."""
    result = detect_frame(blank, blank, cfg)
    assert result.shape == (10, 10)
    assert result.dtype == bool


def test_detect_frame_no_detection_on_identical(blank, cfg):
    """Detect frame returns no detections for identical frames."""
    result = detect_frame(blank, blank, cfg)
    assert not result.any()


def test_detect_frame_detects_bright_spot(blank, cfg):
    """Detect frame detects bright spot in right tile."""
    frame = blank.copy()
    frame[5, 15, 2] = 200
    result = detect_frame(frame, blank, cfg)
    assert result[5, 5]


def test_detect_frame_mask_zeroed(blank, cfg):
    """Detect frame masks out title region."""
    frame = blank.copy()
    frame[0, 3, 2] = 200
    result = detect_frame(frame, blank, cfg)
    assert not result[0, 3]
