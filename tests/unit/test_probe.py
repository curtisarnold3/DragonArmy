"""Tests for pipeline.probe"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from pipeline.probe import probe


def test_probe_returns_correct_metadata(tmp_path):
    """Probe returns correct metadata from synthetic clip."""
    clip = tmp_path / "test.mp4"
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=red:s=320x240:d=0.333333",
        "-vf", "fps=30", "-vframes", "10", "-vcodec", "ffv1", "-pix_fmt", "yuv420p", "-y", str(clip)
    ], check=True, capture_output=True)

    r = probe(clip)
    assert r["width"] == 320 and r["height"] == 240
    assert abs(r["fps"] - 30.0) < 0.1 and r["nb_frames"] == 10


def test_probe_warns_on_dimension_mismatch(tmp_path, caplog):
    """Probe warns but does not raise on dimension mismatch."""
    clip = tmp_path / "test.mp4"
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=red:s=320x240:d=0.333333",
        "-vf", "fps=30", "-vframes", "10", "-vcodec", "ffv1", "-pix_fmt", "yuv420p", "-y", str(clip)
    ], check=True, capture_output=True)

    cfg_path = Path(__file__).parent.parent.parent / "pipeline" / "config.yaml"
    cfg = yaml.safe_load(open(cfg_path))
    cfg["frame"] = {"expected_width": 9999, "expected_height": 240}

    with patch("builtins.open", side_effect=lambda p, *a, **k:
               open(p, *a, **k) if "config.yaml" not in str(p)
               else __import__("io").StringIO(yaml.dump(cfg))):
        with caplog.at_level("WARNING"):
            r = probe(clip)

    assert r["width"] == 320
    assert any("Width mismatch" in rec.message for rec in caplog.records)


def test_probe_raises_on_missing_file():
    """Probe raises on missing file."""
    with pytest.raises(subprocess.CalledProcessError):
        probe("/nonexistent.mp4")
