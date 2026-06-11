"""Tests for pipeline.pipeline"""

import pytest
from unittest.mock import patch
import numpy as np
import datetime
import tempfile


def test_run_calls_progress_callback():
    """Run calls progress callback with expected stages."""
    from pipeline.pipeline import run

    calls = []

    def fake_cb(stage, pct):
        calls.append((stage, pct))

    with patch("pipeline.probe.probe", return_value={"nb_frames": 100, "width": 20, "height": 10}), \
         patch("pipeline.grabber.grab_frame", return_value=np.zeros((10, 20, 3), dtype=np.uint8)), \
         patch("pipeline.calibrate.find_world_width", return_value=10), \
         patch("pipeline.calibrate.build_base_map", return_value=np.zeros((10, 20, 3), dtype=np.uint8)), \
         patch("pipeline.segment.compute_title_diffs", return_value=np.zeros(99)), \
         patch("pipeline.segment.find_segment_boundaries", return_value=[0, 10, 20]), \
         patch("pipeline.segment.assign_times", return_value=[
             {"index": 1, "window_num": 0, "start_frame": 0, "end_frame": 10,
              "rep_frame": 5,
              "utc_start": datetime.datetime(2026, 6, 9, 0, 0, tzinfo=datetime.timezone.utc),
              "utc_end": datetime.datetime(2026, 6, 9, 1, 30, tzinfo=datetime.timezone.utc)}
         ]), \
         patch("pipeline.pipeline._extract_frames"), \
         patch("pipeline.aggregate.accumulate", return_value=np.zeros((10, 10), dtype=np.uint16)), \
         patch("pipeline.aggregate.seam_roll", return_value=(
             np.zeros((10, 10), dtype=np.uint16),
             np.zeros((10, 10, 3), dtype=np.uint8), 0)), \
         patch("pipeline.render.render_hero", return_value=np.zeros((10, 10, 3), dtype=np.uint8)), \
         patch("pipeline.render.render_hourly_snapshots", return_value=[]), \
         patch("pipeline.poster.compose_poster", return_value=np.zeros((100, 10, 3), dtype=np.uint8)), \
         patch("pipeline.poster.save_poster"), \
         patch("cv2.imwrite"), \
         patch("pipeline.render.build_lut", return_value=np.zeros((256, 3), dtype=np.uint8)):

        with tempfile.TemporaryDirectory() as tmp:
            result = run("dummy.mp4", tmp, progress_callback=fake_cb)

    assert len(calls) > 0
    assert calls[0][0] == "probe"
    assert calls[-1][0] == "done"
    assert calls[-1][1] == 100


def test_run_returns_expected_keys():
    """Run returns dict with required keys."""
    from pipeline.pipeline import run

    with patch("pipeline.probe.probe", return_value={"nb_frames": 100, "width": 20, "height": 10}), \
         patch("pipeline.grabber.grab_frame", return_value=np.zeros((10, 20, 3), dtype=np.uint8)), \
         patch("pipeline.calibrate.find_world_width", return_value=10), \
         patch("pipeline.calibrate.build_base_map", return_value=np.zeros((10, 20, 3), dtype=np.uint8)), \
         patch("pipeline.segment.compute_title_diffs", return_value=np.zeros(99)), \
         patch("pipeline.segment.find_segment_boundaries", return_value=[0, 10, 20]), \
         patch("pipeline.segment.assign_times", return_value=[
             {"index": 1, "window_num": 0, "start_frame": 0, "end_frame": 10,
              "rep_frame": 5,
              "utc_start": datetime.datetime(2026, 6, 9, 0, 0, tzinfo=datetime.timezone.utc),
              "utc_end": datetime.datetime(2026, 6, 9, 1, 30, tzinfo=datetime.timezone.utc)}
         ]), \
         patch("pipeline.pipeline._extract_frames"), \
         patch("pipeline.aggregate.accumulate", return_value=np.zeros((10, 10), dtype=np.uint16)), \
         patch("pipeline.aggregate.seam_roll", return_value=(
             np.zeros((10, 10), dtype=np.uint16),
             np.zeros((10, 10, 3), dtype=np.uint8), 0)), \
         patch("pipeline.render.render_hero", return_value=np.zeros((10, 10, 3), dtype=np.uint8)), \
         patch("pipeline.render.render_hourly_snapshots", return_value=[]), \
         patch("pipeline.poster.compose_poster", return_value=np.zeros((100, 10, 3), dtype=np.uint8)), \
         patch("pipeline.poster.save_poster"), \
         patch("cv2.imwrite"), \
         patch("pipeline.render.build_lut", return_value=np.zeros((256, 3), dtype=np.uint8)):

        with tempfile.TemporaryDirectory() as tmp:
            result = run("dummy.mp4", tmp)

    assert "poster_path" in result
    assert "zip_path" in result
    assert "presence_max" in result
    assert "total_detection_pixels" in result
