# face_zoom.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# PROFESSIONAL MICRO ZOOM ENGINE v2.0
# ==========================================================
# Purpose:
# - Old apply_face_zoom(input_video, output_video, mode="LONG")
#   compatibility maintain karna.
# - FFmpeg based safe micro-zoom apply karna.
# - Shorts aur Long dono ke liye subtle zoom levels.
# - AI-generated clips ko over-zoom ya pixel damage se bachana.
#
# Important:
# Is file ka naam face_zoom.py hai, lekin current project mein
# real face detection use nahi ho rahi. Isliye ye "face zoom"
# ke bajaye safe cinematic micro-zoom karta hai.
# ==========================================================

import subprocess
import random
from pathlib import Path


def safe_print(message):
    try:
        print(str(message), flush=True)
    except Exception:
        pass


def _normalize_mode(mode):
    mode = str(mode or "LONG").strip().upper()
    if mode in ("SHORT", "SHORTS", "REEL", "REELS"):
        return "SHORT"
    return "LONG"


def _choose_zoom(mode):
    """
    Professional safe zoom values.

    Shorts:
        slightly stronger because mobile screen chhoti hoti hai.

    Long:
        softer because horizontal frame mein over-zoom obvious lagta hai.
    """
    mode = _normalize_mode(mode)

    if mode == "SHORT":
        return random.choice([1.025, 1.035, 1.045, 1.055])

    return random.choice([1.012, 1.018, 1.025, 1.032])


def apply_face_zoom(input_video, output_video, mode="LONG", zoom = True):
    """
    Old-compatible function.

    Args:
        input_video: source video path.
        output_video: output video path.
        mode: SHORT or LONG.
        zoom: optional manual zoom factor.

    Returns:
        output video path.
    """
    input_video = Path(input_video)
    output_video = Path(output_video)

    if not input_video.exists():
        raise FileNotFoundError(f"Input video not found: {input_video}")

    output_video.parent.mkdir(parents=True, exist_ok=True)

    mode = _normalize_mode(mode)

    if zoom is None:
        zoom = _choose_zoom(mode)

    zoom = max(1.0, min(float(zoom), 1.08))

    vf = (
        f"scale=iw*{zoom}:ih*{zoom},"
        f"crop=iw/{zoom}:ih/{zoom},"
        f"scale=iw:ih,"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_video),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "19",
        "-c:a", "copy",
        str(output_video),
    ]

    safe_print(
        f"[FaceZoom] Applying safe micro zoom | mode={mode} | zoom={zoom}"
    )

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False
    )

    if result.returncode != 0:
        safe_print(result.stderr)
        raise RuntimeError("Face zoom FFmpeg command failed.")

    return str(output_video)


if __name__ == "__main__":
    print("Face Zoom Engine ready.")