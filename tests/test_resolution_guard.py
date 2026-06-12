"""Test resolution validation guards in pipeline/segment.py"""

import pytest
import cv2
import numpy as np
import tempfile
from pathlib import Path
import yaml

from pipeline.segment import compute_title_diffs, assign_times


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
