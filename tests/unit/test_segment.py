"""Tests for pipeline.segment"""

import numpy as np
import pytest
from datetime import datetime, timezone, timedelta

from pipeline.segment import find_segment_boundaries, assign_times


def test_find_segment_boundaries_detects_spikes():
    """Find segment boundaries detects spikes above threshold."""
    diffs = np.zeros(100)
    diffs[10] = 9.0   # transition at frame 10
    diffs[30] = 9.0   # transition at frame 30
    diffs[50] = 9.0   # transition at frame 50
    diffs[70] = 9.0   # transition at frame 70
    diffs[90] = 9.0   # transition at frame 90
    boundaries = find_segment_boundaries(diffs, threshold=0.5)
    starts = [s for s, e in boundaries]
    assert 0 in starts
    assert len(boundaries) >= 4


def test_find_segment_boundaries_no_spikes():
    """Find segment boundaries with no spikes raises ValueError for < 4 segments."""
    diffs = np.zeros(30)   # 30 frames, no spikes
    with pytest.raises(ValueError) as exc_info:
        find_segment_boundaries(diffs, threshold=0.5)
    assert "only 1 segments" in str(exc_info.value)


def test_find_segment_boundaries_returns_sorted():
    """Find segment boundaries returns sorted list."""
    diffs = np.zeros(100)
    diffs[10] = 9.0
    diffs[30] = 9.0
    diffs[50] = 9.0
    diffs[70] = 9.0
    boundaries = find_segment_boundaries(diffs, threshold=0.5)
    starts = [s for s, e in boundaries]
    assert starts == sorted(starts)


def test_assign_times_first_window():
    """Assign times correctly labels first window."""
    seg_tuples = [(0, 10), (10, 20), (20, 30), (30, 40)]
    config = {
        "time_model": {
            "origin_utc": "2026-06-09T00:00:00Z",
            "window_lookback_min": 90,
            "step_min": 10,
            "intro_segment": 0,
        },
        "segmentation": {"representative_position": 0.55}
    }
    segments = assign_times(seg_tuples, config)

    first = segments[0]
    expected_start = datetime(2026, 6, 9, 0, 0, tzinfo=timezone.utc)
    assert first["utc_start"] == expected_start
    assert first["utc_end"] == expected_start + timedelta(minutes=90)


def test_assign_times_skips_intro():
    """Assign times skips intro segment."""
    seg_tuples = [(0, 10), (10, 20), (20, 30), (30, 40)]
    config = {
        "time_model": {
            "origin_utc": "2026-06-09T00:00:00Z",
            "window_lookback_min": 90,
            "step_min": 10,
            "intro_segment": 0,
        },
        "segmentation": {"representative_position": 0.55}
    }
    segments = assign_times(seg_tuples, config)

    indices = [s["index"] for s in segments]
    assert 0 not in indices
    assert len(segments) == 3
