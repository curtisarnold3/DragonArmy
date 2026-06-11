"""Frame grabber using ffmpeg."""

import subprocess
from pathlib import Path

import numpy as np

from pipeline.probe import probe


def grab_frame(mp4_path: str | Path, frame_index: int, width: int = None, height: int = None) -> np.ndarray:
    """Extract a single frame as BGR uint8 array (H, W, 3)."""
    if width is None or height is None:
        meta = probe(mp4_path)
        width = meta["width"]
        height = meta["height"]
        nb_frames = meta["nb_frames"]
        if frame_index < 0 or frame_index >= nb_frames:
            raise ValueError(f"Frame index {frame_index} out of range [0, {nb_frames})")

    result = subprocess.run([
        "ffmpeg", "-i", str(mp4_path), "-vf", f"select='eq(n\\,{frame_index})'",
        "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1"
    ], capture_output=True, check=True)

    frame = np.frombuffer(result.stdout, dtype=np.uint8)
    return frame.reshape(height, width, 3)
