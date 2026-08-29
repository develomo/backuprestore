"""
===============================================================
LONG VIDEO POST PROCESSOR
Part 1
Author : ChatGPT
Purpose:
    Long Video Final Processing Engine

Modules Started:
    ✓ FFmpeg Detection
    ✓ Logger
    ✓ Utility Functions
    ✓ Video Duration
    ✓ Audio Duration
    ✓ Safe Command Runner
    ✓ File Validation
===============================================================
"""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import tempfile
import random
import time

from pathlib import Path
from typing import Optional, List

# -------------------------------------------------------------
# FFmpeg Detection
# -------------------------------------------------------------

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

FFPROBE = str(
    Path(FFMPEG).with_name("ffprobe.exe")
) if Path(FFMPEG).name.lower() == "ffmpeg.exe" else "ffprobe"

# -------------------------------------------------------------
# Logger
# -------------------------------------------------------------

def log(message: str):

    now = time.strftime("%H:%M:%S")

    print(f"[LongPost][{now}] {message}", flush=True)

# -------------------------------------------------------------
# Safe Command Runner
# -------------------------------------------------------------

def run_cmd(cmd: list):

    cmd = [str(x) for x in cmd]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="ignore"
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr[-4000:])

    return result

# -------------------------------------------------------------
# File Exists Check
# -------------------------------------------------------------

def ensure_file(path):

    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(p)

    return p

# -------------------------------------------------------------
# Video Duration
# -------------------------------------------------------------

def video_duration(video):

    video = ensure_file(video)

    try:

        result = subprocess.run(
            [
                FFPROBE,
                "-v","error",
                "-show_entries","format=duration",
                "-of","default=nw=1:nk=1",
                str(video)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="ignore"
        )

        return float(result.stdout.strip())

    except Exception:

        return 0.0

# -------------------------------------------------------------
# Audio Duration
# -------------------------------------------------------------

def audio_duration(audio):

    audio = ensure_file(audio)

    try:

        result = subprocess.run(
            [
                FFPROBE,
                "-v","error",
                "-show_entries","format=duration",
                "-of","default=nw=1:nk=1",
                str(audio)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="ignore"
        )

        return float(result.stdout.strip())

    except Exception:

        return 0.0

# ---------------------- END PART 1 ----------------------------