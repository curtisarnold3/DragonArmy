"""Golden master diagnostic — runs full pipeline and reports
key metrics. Run inside Docker container:
  docker run --rm -v $PWD/tests:/app/tests \
    -e PYTHONPATH=/app -w /app gnss-agg:ci \
    python3 tests/integration/run_golden_check.py
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

MP4 = "tests/golden/deep-haerts-video_2026-06-10T15_52_21.682Z.mp4"
OUT = "/tmp/golden_check_output"

if not Path(MP4).exists():
    print(f"ERROR: Reference MP4 not found at {MP4}")
    print("Make sure git-lfs has pulled the file.")
    sys.exit(1)

print(f"Running full pipeline on {MP4}")
print(f"Output dir: {OUT}")
print()

from pipeline.pipeline import run

def progress_cb(stage, pct):
    print(f"  [{pct:3d}%] {stage}")

result = run(MP4, OUT, progress_callback=progress_cb)

print()
print("=== GOLDEN MASTER CHECK ===")
print(f"presence_max:            {result['presence_max']}")
print(f"total_detection_pixels:  {result['total_detection_pixels']}")
print()
print(f"Expected presence_max:           57")
print(f"Expected total_detection_pixels: 29538")
print()

peak_ok = result['presence_max'] in (57, 58, 59)
total_ok = abs(result['total_detection_pixels'] - 29538) < 500

print(f"presence_max match:     {'OK' if peak_ok else 'MISMATCH'}")
print(f"total_detection match:  {'OK' if total_ok else 'MISMATCH'}")

if peak_ok and total_ok:
    print()
    print("GOLDEN MASTER: PASS")
    sys.exit(0)
else:
    print()
    print("GOLDEN MASTER: FAIL")
    sys.exit(1)
