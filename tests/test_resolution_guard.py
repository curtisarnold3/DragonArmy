"""Test resolution validation guards in pipeline/segment.py"""

import pytest
import cv2
import numpy as np
import tempfile
from pathlib import Path
import yaml

from pipeline.segment import compute_title_diffs, assign_times


def test_resolution_mismatch_caught():
    """Verify that a video with wrong resolution raises clear error"""
    # Create a fake 1920x1080 mp4 (wrong resolution)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        # Write 10 black frames at 1920x1080
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(tmp_path), fourcc, 30.0, (1920, 1080))
        black_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        for _ in range(10):
            out.write(black_frame)
        out.release()

        # Load real config
        config_path = Path(__file__).parent.parent / "pipeline" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Attempt to process - should raise ValueError with "Layout mismatch"
        with pytest.raises(ValueError) as exc_info:
            compute_title_diffs(tmp_path, config)

        assert "Layout mismatch" in str(exc_info.value)
        assert "1920×1080" in str(exc_info.value)
        assert "2560×1198" in str(exc_info.value)

    finally:
        tmp_path.unlink()


def test_zero_windows_caught():
    """Verify that zero segments raises clear error"""
    # Load real config
    config_path = Path(__file__).parent.parent / "pipeline" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Call assign_times with empty segment list
    with pytest.raises(ValueError) as exc_info:
        assign_times([], config)

    assert "0 windows" in str(exc_info.value)
    assert "expected layout" in str(exc_info.value)
