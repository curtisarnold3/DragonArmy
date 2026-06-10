"""Frame grabber using ffmpeg."""

import subprocess
from pathlib import Path

import numpy as np

from pipeline.probe import probe


def grab_frame(mp4_path: str | Path, frame_index: int) -> np.ndarray:
    """Extract a single frame as BGR uint8 array (H, W, 3)."""
    meta = probe(mp4_path)
    if frame_index < 0 or frame_index >= meta["nb_frames"]:
        raise ValueError(f"Frame index {frame_index} out of range [0, {meta['nb_frames']})")

    result = subprocess.run([
        "ffmpeg", "-i", str(mp4_path), "-vf", f"select='eq(n\\,{frame_index})'",
        "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1"
    ], capture_output=True, check=True)

    frame = np.frombuffer(result.stdout, dtype=np.uint8)
    return frame.reshape(meta["height"], meta["width"], 3)
