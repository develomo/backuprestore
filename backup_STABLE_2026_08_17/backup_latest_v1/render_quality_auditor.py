# render_quality_auditor.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# RENDER QUALITY AUDITOR v1.0
# ==========================================================
# Purpose:
# - Render ke baad automatic quality check.
# - Overexposure / white blown frames detect kare.
# - Audio loudness info read kare.
# - Resolution/FPS/duration validate kare.
# - Caption/text delay ka basic diagnostic support.
# - Final score/report generate kare.
#
# This is not a replacement for human review.
# It is a backend safety checker to catch big technical bugs.
# ==========================================================

import json
import subprocess
import statistics
from pathlib import Path
from datetime import datetime

import numpy as np


BASE_DIR = Path(__file__).parent
AUDIT_DIR = BASE_DIR / "outputs" / "audit_reports"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# TARGETS
# ==========================================================

TARGETS = {
    "short": {
        "width": 2160,
        "height": 3840,
        "fps_min": 23,
        "fps_max": 31,
        "target_lufs": -14.0,
        "lufs_tolerance": 2.0,
        "max_white_frame_ratio": 0.45,
        "max_avg_brightness": 225,
        "min_duration": 5,
        "max_duration": 180,
    },
    "long": {
        "width": 3840,
        "height": 2160,
        "fps_min": 23,
        "fps_max": 31,
        "target_lufs": -14.0,
        "lufs_tolerance": 2.5,
        "max_white_frame_ratio": 0.42,
        "max_avg_brightness": 225,
        "min_duration": 30,
        "max_duration": 7200,
    },
}


# ==========================================================
# UTILS
# ==========================================================

def safe_print(message):
    try:
        print(str(message), flush=True)
    except Exception:
        pass


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _run_command(cmd):
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False
    )
    return result.stdout, result.stderr, result.returncode


def _parse_fraction(value):
    value = str(value or "").strip()

    if "/" in value:
        a, b = value.split("/", 1)
        b = _safe_float(b, 1.0)
        if b == 0:
            return 0.0
        return _safe_float(a, 0.0) / b

    return _safe_float(value, 0.0)


def _mode_key(mode):
    mode = str(mode or "short").lower()
    return "long" if mode == "long" else "short"


# ==========================================================
# MEDIA INFO
# ==========================================================

def get_media_info(video_path):
    """
    Reads media metadata using ffprobe.
    """
    video_path = Path(video_path)

    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(video_path),
    ]

    stdout, stderr, code = _run_command(cmd)

    if code != 0:
        raise RuntimeError(f"ffprobe failed: {stderr}")

    data = json.loads(stdout)

    video_stream = None
    audio_stream = None

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        if stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream

    if not video_stream:
        raise RuntimeError("No video stream found.")

    info = {
        "path": str(video_path),
        "format_duration": _safe_float(data.get("format", {}).get("duration"), 0.0),
        "size_bytes": _safe_int(data.get("format", {}).get("size"), 0),
        "bitrate": _safe_int(data.get("format", {}).get("bit_rate"), 0),
        "video": {
            "width": _safe_int(video_stream.get("width")),
            "height": _safe_int(video_stream.get("height")),
            "codec": video_stream.get("codec_name"),
            "fps": _parse_fraction(video_stream.get("avg_frame_rate")),
            "duration": _safe_float(video_stream.get("duration"), 0.0),
            "pix_fmt": video_stream.get("pix_fmt"),
        },
        "audio": None,
    }

    if audio_stream:
        info["audio"] = {
            "codec": audio_stream.get("codec_name"),
            "sample_rate": _safe_int(audio_stream.get("sample_rate")),
            "channels": _safe_int(audio_stream.get("channels")),
            "duration": _safe_float(audio_stream.get("duration"), 0.0),
            "bitrate": _safe_int(audio_stream.get("bit_rate"), 0),
        }

    return info


# ==========================================================
# FRAME EXPOSURE AUDIT
# ==========================================================

def sample_frame_brightness(video_path, sample_count=12):
    """
    Samples frames using ffmpeg rawvideo and computes brightness.

    Returns:
        dict with brightness stats.
    """
    video_path = Path(video_path)
    info = get_media_info(video_path)

    duration = info["format_duration"] or info["video"]["duration"]
    width = info["video"]["width"]
    height = info["video"]["height"]

    if duration <= 0 or width <= 0 or height <= 0:
        return {
            "samples": [],
            "avg_brightness": 0,
            "max_brightness": 0,
            "white_frame_ratio": 0,
            "overexposed_samples": 0,
        }

    times = []
    if sample_count <= 1:
        times = [min(duration * 0.5, duration - 0.1)]
    else:
        for i in range(sample_count):
            t = duration * (i + 1) / (sample_count + 1)
            times.append(max(0.05, min(t, duration - 0.05)))

    samples = []

    # Downscale for speed before raw extraction.
    sample_w = 160
    sample_h = max(90, int(sample_w * height / max(width, 1)))

    for t in times:
        cmd = [
            "ffmpeg",
            "-v", "error",
            "-ss", str(round(t, 3)),
            "-i", str(video_path),
            "-frames:v", "1",
            "-vf", f"scale={sample_w}:{sample_h}",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-",
        ]

        try:
            raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            frame = np.frombuffer(raw, dtype=np.uint8)

            expected = sample_w * sample_h * 3
            if frame.size < expected:
                continue

            frame = frame[:expected].reshape((sample_h, sample_w, 3))

            brightness = frame.mean()
            white_pixels = np.mean(np.all(frame > 245, axis=2))
            highlight_pixels = np.mean(frame.mean(axis=2) > 235)

            samples.append({
                "time": round(t, 3),
                "avg_brightness": round(float(brightness), 3),
                "white_pixel_ratio": round(float(white_pixels), 4),
                "highlight_ratio": round(float(highlight_pixels), 4),
                "overexposed": bool(brightness > 230 or white_pixels > 0.45),
            })

        except Exception as e:
            samples.append({
                "time": round(t, 3),
                "error": str(e),
            })

    valid = [s for s in samples if "avg_brightness" in s]

    if not valid:
        return {
            "samples": samples,
            "avg_brightness": 0,
            "max_brightness": 0,
            "white_frame_ratio": 0,
            "overexposed_samples": 0,
        }

    avg_brightness = statistics.mean(s["avg_brightness"] for s in valid)
    max_brightness = max(s["avg_brightness"] for s in valid)
    overexposed = sum(1 for s in valid if s.get("overexposed"))
    white_frame_ratio = overexposed / max(len(valid), 1)

    return {
        "samples": samples,
        "avg_brightness": round(float(avg_brightness), 3),
        "max_brightness": round(float(max_brightness), 3),
        "white_frame_ratio": round(float(white_frame_ratio), 4),
        "overexposed_samples": overexposed,
        "valid_samples": len(valid),
    }


# ==========================================================
# AUDIO LOUDNESS AUDIT
# ==========================================================

def measure_loudness(video_path):
    """
    Uses ffmpeg loudnorm analysis mode.
    Returns approximate loudness values if available.
    """
    video_path = Path(video_path)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i", str(video_path),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
        "-f", "null",
        "-",
    ]

    stdout, stderr, code = _run_command(cmd)
    text = stdout + "\n" + stderr

    start = text.rfind("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return {
            "available": False,
            "error": "Could not parse loudnorm output.",
        }

    try:
        data = json.loads(text[start:end + 1])
        return {
            "available": True,
            "input_i": _safe_float(data.get("input_i")),
            "input_tp": _safe_float(data.get("input_tp")),
            "input_lra": _safe_float(data.get("input_lra")),
            "input_thresh": _safe_float(data.get("input_thresh")),
            "target_offset": _safe_float(data.get("target_offset")),
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


# ==========================================================
# VALIDATION
# ==========================================================

def validate_media_info(info, mode="short"):
    mode = _mode_key(mode)
    target = TARGETS[mode]

    warnings = []
    errors = []

    width = info["video"]["width"]
    height = info["video"]["height"]
    fps = info["video"]["fps"]
    duration = info["format_duration"] or info["video"]["duration"]

    if width != target["width"] or height != target["height"]:
        warnings.append(
            f"Resolution is {width}x{height}; target is "
            f"{target['width']}x{target['height']}."
        )

    if not (target["fps_min"] <= fps <= target["fps_max"]):
        warnings.append(f"FPS is {fps:.2f}; expected around 24-30.")

    if duration < target["min_duration"]:
        warnings.append(f"Duration is very short: {duration:.2f}s.")

    if duration > target["max_duration"]:
        errors.append(f"Duration exceeds mode limit: {duration:.2f}s.")

    if not info.get("audio"):
        errors.append("No audio stream found.")

    if info.get("bitrate", 0) <= 0:
        warnings.append("Bitrate not detected.")

    return {
        "errors": errors,
        "warnings": warnings,
    }


def validate_exposure(exposure, mode="short"):
    mode = _mode_key(mode)
    target = TARGETS[mode]

    warnings = []
    errors = []

    avg = exposure.get("avg_brightness", 0)
    white_ratio = exposure.get("white_frame_ratio", 0)

    if avg > target["max_avg_brightness"]:
        errors.append(
            f"Average brightness too high: {avg}. Possible overexposure."
        )

    if white_ratio > target["max_white_frame_ratio"]:
        errors.append(
            f"Too many blown/white frames: {white_ratio:.2%}."
        )

    if exposure.get("overexposed_samples", 0) > 0:
        warnings.append(
            f"{exposure.get('overexposed_samples')} sampled frames look overexposed."
        )

    return {
        "errors": errors,
        "warnings": warnings,
    }


def validate_loudness(loudness, mode="short"):
    mode = _mode_key(mode)
    target = TARGETS[mode]

    warnings = []
    errors = []

    if not loudness.get("available"):
        warnings.append("Audio loudness could not be measured.")
        return {
            "errors": errors,
            "warnings": warnings,
        }

    lufs = loudness.get("input_i", 0.0)
    target_lufs = target["target_lufs"]
    tolerance = target["lufs_tolerance"]

    if abs(lufs - target_lufs) > tolerance:
        warnings.append(
            f"Audio loudness is {lufs:.1f} LUFS; target is around {target_lufs:.1f} LUFS."
        )

    return {
        "errors": errors,
        "warnings": warnings,
    }


# ==========================================================
# SCORE
# ==========================================================

def compute_quality_score(media_check, exposure_check, loudness_check):
    """
    Gives simple 0-100 backend technical score.
    """
    score = 100

    score -= len(media_check.get("errors", [])) * 18
    score -= len(media_check.get("warnings", [])) * 6

    score -= len(exposure_check.get("errors", [])) * 22
    score -= len(exposure_check.get("warnings", [])) * 8

    score -= len(loudness_check.get("errors", [])) * 12
    score -= len(loudness_check.get("warnings", [])) * 6

    return max(0, min(100, score))


# ==========================================================
# MAIN AUDIT
# ==========================================================

def audit_render(video_path, mode="short", expected_duration=None, save_report=True):
    """
    Full render audit.

    Returns:
        dict audit report.
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    safe_print(f"[RenderQualityAuditor] Auditing: {video_path.name}")

    info = get_media_info(video_path)
    exposure = sample_frame_brightness(video_path, sample_count=12)
    loudness = measure_loudness(video_path)

    media_check = validate_media_info(info, mode=mode)
    exposure_check = validate_exposure(exposure, mode=mode)
    loudness_check = validate_loudness(loudness, mode=mode)

    duration_warning = None
    if expected_duration:
        actual_duration = info["format_duration"] or info["video"]["duration"]
        diff = abs(float(actual_duration) - float(expected_duration))
        if diff > 0.35:
            duration_warning = (
                f"Output duration differs from expected by {diff:.2f}s."
            )
            media_check["warnings"].append(duration_warning)

    score = compute_quality_score(media_check, exposure_check, loudness_check)

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "video_path": str(video_path),
        "mode": _mode_key(mode),
        "technical_score": score,
        "status": "pass" if score >= 85 and not media_check["errors"] and not exposure_check["errors"] else "review",
        "media_info": info,
        "exposure": exposure,
        "loudness": loudness,
        "checks": {
            "media": media_check,
            "exposure": exposure_check,
            "loudness": loudness_check,
        },
        "summary": build_summary(score, media_check, exposure_check, loudness_check),
    }

    if save_report:
        report_path = save_audit_report(report)
        report["report_path"] = str(report_path)

    safe_print(
        f"[RenderQualityAuditor] Score: {score}/100 | Status: {report['status']}"
    )

    return report


def build_summary(score, media_check, exposure_check, loudness_check):
    problems = []
    warnings = []

    for section in (media_check, exposure_check, loudness_check):
        problems.extend(section.get("errors", []))
        warnings.extend(section.get("warnings", []))

    if score >= 92 and not problems:
        verdict = "Excellent technical render."
    elif score >= 85 and not problems:
        verdict = "Good render with minor warnings."
    elif score >= 70:
        verdict = "Needs review before upload."
    else:
        verdict = "Technical issues detected. Re-render recommended."

    return {
        "verdict": verdict,
        "problem_count": len(problems),
        "warning_count": len(warnings),
        "problems": problems,
        "warnings": warnings,
    }


def save_audit_report(report):
    video_name = Path(report["video_path"]).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = AUDIT_DIR / f"{video_name}_audit_{timestamp}.json"

    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return path


# ==========================================================
# DEBUG
# ==========================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python render_quality_auditor.py video.mp4")
    else:
        result = audit_render(sys.argv[1], mode="short")
        print(json.dumps(result["summary"], indent=2))