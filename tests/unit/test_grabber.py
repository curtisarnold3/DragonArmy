"""Tests for pipeline.grabber"""

import pytest

from pipeline.grabber import grab_frame


def test_grab_frame_returns_correct_shape_and_color(synthetic_clip):
    """Grab frame returns correct shape and color."""
    frame = grab_frame(synthetic_clip, 0)

    assert frame.shape == (240, 320, 3)
    # Center pixel should be red in BGR: B<10, G<10, R>245
    b, g, r = frame[120, 160]
    assert b < 10 and g < 10 and r > 245


def test_grab_frame_raises_on_out_of_range(synthetic_clip):
    """Grab frame raises ValueError for out-of-range indices."""
    with pytest.raises(ValueError, match="out of range"):
        grab_frame(synthetic_clip, -1)
    with pytest.raises(ValueError, match="out of range"):
        grab_frame(synthetic_clip, 10)
