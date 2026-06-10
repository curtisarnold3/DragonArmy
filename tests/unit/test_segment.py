"""Tests for pipeline.segment"""

import numpy as np
import pytest
from datetime import datetime, timezone, timedelta

from pipeline.segment import find_segment_boundaries, assign_times


def test_find_segment_boundaries_detects_spikes():
    """Find segment boundaries detects spikes above threshold."""
    diffs = np.array([0.1, 0.2, 5.0, 0.1, 0.1, 6.0, 0.2])
    boundaries = find_segment_boundaries(diffs, threshold=0.5)
    assert 0 in boundaries
    assert 3 in boundaries
    assert 6 in boundaries


def test_find_segment_boundaries_no_spikes():
    """Find segment boundaries with no spikes returns only initial boundary."""
    diffs = np.array([0.1, 0.2, 0.1, 0.3])
    boundaries = find_segment_boundaries(diffs, threshold=0.5)
    assert boundaries == [0]


def test_find_segment_boundaries_returns_sorted():
    """Find segment boundaries returns sorted list."""
    diffs = np.array([0.1, 6.0, 0.1, 5.0, 0.1])
    boundaries = find_segment_boundaries(diffs, threshold=0.5)
    assert boundaries == sorted(boundaries)


def test_assign_times_first_window():
    """Assign times correctly labels first window."""
    boundaries = [0, 10, 20, 30]
    config = {
        "time_model": {
            "origin_utc": "2026-06-09T00:00:00Z",
            "window_lookback_min": 90,
            "step_min": 10,
            "intro_segment": 0,
        }
    }
    segments = assign_times(boundaries, config)

    first = segments[0]
    expected_start = datetime(2026, 6, 9, 0, 0, tzinfo=timezone.utc)
    assert first["utc_start"] == expected_start
    assert first["utc_end"] == expected_start + timedelta(minutes=90)


def test_assign_times_skips_intro():
    """Assign times skips intro segment."""
    boundaries = [0, 10, 20, 30]
    config = {
        "time_model": {
            "origin_utc": "2026-06-09T00:00:00Z",
            "window_lookback_min": 90,
            "step_min": 10,
            "intro_segment": 0,
        }
    }
    segments = assign_times(boundaries, config)

    indices = [s["index"] for s in segments]
    assert 0 not in indices
    assert len(segments) == 3
