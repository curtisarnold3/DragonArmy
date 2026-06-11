"""Tests for pipeline.poster"""

import numpy as np
import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from pipeline.poster import compose_poster


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
        },
        "poster": {"crop": {"y_top": 0, "y_bottom": 100}},
        "hourly": {"cadence_steps": 6},
        "segmentation": {"representative_position": 0.55},
    }


@pytest.fixture
def hero():
    return np.zeros((200, 400, 3), dtype=np.uint8)


@pytest.fixture
def presence():
    p = np.zeros((100, 200), dtype=np.uint16)
    p[50, 100] = 10
    return p


@pytest.fixture
def segments():
    base = datetime(2026, 6, 9, 0, 0, tzinfo=timezone.utc)
    return [
        {
            "index": i + 1,
            "window_num": i,
            "start_frame": i * 10,
            "end_frame": (i + 1) * 10,
            "utc_start": base + timedelta(minutes=i * 10),
            "utc_end": base + timedelta(minutes=i * 10 + 90),
        }
        for i in range(6)
    ]


def test_compose_poster_returns_ndarray(hero, segments, presence, config):
    """Compose poster returns numpy array."""
    result = compose_poster(hero, [], segments, presence, config)
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.uint8
    assert result.ndim == 3


def test_compose_poster_width_matches_hero(hero, segments, presence, config):
    """Compose poster width matches hero width."""
    result = compose_poster(hero, [], segments, presence, config)
    assert result.shape[1] == hero.shape[1]


def test_compose_poster_height_greater_than_hero(hero, segments, presence, config):
    """Compose poster is taller than hero alone."""
    result = compose_poster(hero, [], segments, presence, config)
    # Poster has banner + hero + legend + grid + footer
    assert result.shape[0] > hero.shape[0]


def test_compose_poster_not_all_black(hero, segments, presence, config):
    """Compose poster has non-black pixels."""
    result = compose_poster(hero, [], segments, presence, config)
    # Background is [15,15,20] so sum should be > 0
    assert result.sum() > 0
