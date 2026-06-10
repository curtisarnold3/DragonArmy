"""Video probe using ffprobe."""

import json
import logging
import subprocess
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def probe(mp4_path: str | Path) -> dict:
    """Extract video metadata. Returns: width, height, fps, nb_frames, duration."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(mp4_path)],
        capture_output=True, text=True, check=True
    )
    data = json.loads(result.stdout)
    vs = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if not vs:
        raise ValueError("No video stream")

    width, height = int(vs["width"]), int(vs["height"])
    num, denom = map(int, vs["avg_frame_rate"].split("/"))
    fps = round(num / denom, 6)
    duration = float(vs.get("duration", 0))
    nb_frames = int(vs["nb_frames"]) if vs.get("nb_frames") and int(vs["nb_frames"]) > 0 else int(duration * fps)

    # Validate against config if frame dims present
    with open(Path(__file__).parent / "config.yaml") as f:
        cfg = yaml.safe_load(f)
    if "frame" in cfg:
        ew, eh = cfg["frame"].get("expected_width"), cfg["frame"].get("expected_height")
        if ew and width != ew:
            logger.warning(f"Width mismatch: actual={width}, expected={ew}")
        if eh and height != eh:
            logger.warning(f"Height mismatch: actual={height}, expected={eh}")

    return {"width": width, "height": height, "fps": fps, "nb_frames": nb_frames, "duration": duration}
