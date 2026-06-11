"""Tests for pipeline.render"""

import numpy as np
import pytest
from unittest.mock import patch

from pipeline.render import build_lut, render_hero


@pytest.fixture
def config():
    return {
        "render": {
            "colormap": [
                [0.0, [0, 0, 255]],
                [1.0, [255, 0, 0]],
            ],
            "gamma": 0.7,
            "overlay_alpha": 0.6,
        }
    }


def test_build_lut_shape(config):
    """Build LUT returns correct shape and dtype."""
    lut = build_lut(config)
    assert lut.shape == (256, 3)
    assert lut.dtype == np.uint8


def test_build_lut_endpoints(config):
    """Build LUT maps endpoints correctly in BGR order."""
    lut = build_lut(config)
    # First stop [0,0,255] is R=0,G=0,B=255 → BGR = [255,0,0]
    assert lut[0, 0] == 255  # B=255
    assert lut[0, 1] == 0    # G=0
    assert lut[0, 2] == 0    # R=0
    # Last stop [255,0,0] is R=255,G=0,B=0 → BGR = [0,0,255]
    assert lut[255, 0] == 0    # B=0
    assert lut[255, 1] == 0    # G=0
    assert lut[255, 2] == 255  # R=255


def test_render_hero_shape(config):
    """Render hero returns correct shape and dtype."""
    H, WW = 10, 20
    presence = np.zeros((H, WW), dtype=np.uint16)
    background = np.zeros((H, WW, 3), dtype=np.uint8)
    result = render_hero(presence, background, config)
    assert result.shape == (H, WW, 3)
    assert result.dtype == np.uint8


def test_render_hero_zero_presence_returns_background(config):
    """Render hero with zero presence returns unmodified background."""
    background = np.ones((10, 20, 3), dtype=np.uint8) * 128
    presence = np.zeros((10, 20), dtype=np.uint16)
    result = render_hero(presence, background, config)
    assert np.array_equal(result, background)


def test_render_hero_detection_changes_pixels(config):
    """Render hero with detections modifies detected pixels."""
    background = np.zeros((10, 20, 3), dtype=np.uint8)
    presence = np.zeros((10, 20), dtype=np.uint16)
    presence[5, 10] = 5
    result = render_hero(presence, background, config)
    # Detected pixel should not be pure black anymore
    assert result[5, 10].sum() > 0
    # Undetected pixels should still be black
    assert result[0, 0].sum() == 0
