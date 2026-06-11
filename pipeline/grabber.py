"""Frame grabber using ffmpeg."""

import logging
import subprocess
from pathlib import Path

import numpy as np

from pipeline.probe import probe

logger = logging.getLogger(__name__)


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


def grab_frames_batch(mp4_path, frame_indices: list[int], width: int = None, height: int = None) -> dict:
    """Extract multiple frames in one ffmpeg pass. Returns dict mapping frame_index -> BGR array."""
    if width is None or height is None:
        meta = probe(mp4_path)
        width, height = meta["width"], meta["height"]

    indices = sorted(set(frame_indices))
    select_expr = "+".join(f"eq(n\\,{i})" for i in indices)

    cmd = [
        "ffmpeg", "-i", str(mp4_path),
        "-vf", f"select='{select_expr}'",
        "-vsync", "0",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "pipe:1"
    ]
    result = subprocess.run(cmd, capture_output=True, check=True)

    frame_size = height * width * 3
    raw = result.stdout
    frames = {}
    for i, idx in enumerate(indices):
        start = i * frame_size
        chunk = raw[start : start + frame_size]
        if len(chunk) == frame_size:
            frames[idx] = np.frombuffer(chunk, dtype=np.uint8).reshape((height, width, 3)).copy()

    logger.info(f"Batch extracted {len(frames)} frames in one ffmpeg pass")
    return frames
