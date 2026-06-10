"""Shared fixtures for unit tests."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def synthetic_clip(tmp_path):
    """Generate a 10-frame 320x240 solid-red clip at 30fps."""
    clip = tmp_path / "test.mp4"
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=red:s=320x240:d=0.333333",
        "-vf", "fps=30", "-vframes", "10", "-vcodec", "ffv1",
        "-y", str(clip)
    ], check=True, capture_output=True)
    return clip
