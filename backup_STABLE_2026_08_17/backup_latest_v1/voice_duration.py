import json
import math
import subprocess
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs" / "voice_duration"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

MIN_DURATION = 0.03
SHORT_LIMIT_SECONDS = 90.0
SHORT_SAFE_LIMIT_SECONDS = 89.5
LONG_MIN_SECONDS = 120.0


def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-").replace("–", "-"), flush=True)
    except Exception:
        pass


def _path(path):
    return Path(path)


def _exists(path):
    try:
        return Path(path).exists()
    except Exception:
        return False


def _validate_file(path, kind="file"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{kind} not found: {p}")
    if not p.is_file():
        raise FileNotFoundError(f"{kind} is not a file: {p}")
    return p


def _is_audio(path):
    return Path(path).suffix.lower() in AUDIO_EXTS


def _is_video(path):
    return Path(path).suffix.lower() in VIDEO_EXTS


def _run(cmd, label="command"):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        safe_print(result.stderr)
        raise RuntimeError(f"{label} failed")
    return result.stdout


def ffprobe_json(path):
    p = _validate_file(path)
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json",
        str(p),
    ]
    try:
        out = _run(cmd, label="ffprobe_json")
        return json.loads(out)
    except Exception:
        return {}


def ffprobe_duration(path):
    p = _validate_file(path)
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(p),
    ]
    try:
        out = _run(cmd, label="ffprobe_duration")
        data = json.loads(out)
        return float(data.get("format", {}).get("duration", 0.0) or 0.0)
    except Exception:
        return 0.0


def wav_duration(path):
    p = Path(path)
    if p.suffix.lower() != ".wav" or not p.exists():
        return 0.0
    try:
        with wave.open(str(p), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return float(frames) / float(rate) if rate else 0.0
    except Exception:
        return 0.0


def moviepy_duration(path):
    p = _validate_file(path)
    try:
        if _is_audio(p):
            from moviepy.editor import AudioFileClip
            clip = AudioFileClip(str(p))
        else:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(str(p))
        duration = float(clip.duration or 0.0)
        try:
            clip.close()
        except Exception:
            pass
        return duration
    except Exception:
        return 0.0


def get_voice_duration_float(path):
    p = _validate_file(path, "voice")
    duration = 0.0
    if p.suffix.lower() == ".wav":
        duration = wav_duration(p)
    if duration <= 0:
        duration = ffprobe_duration(p)
    if duration <= 0:
        duration = moviepy_duration(p)
    if duration <= 0:
        raise RuntimeError(f"Could not read voice duration: {p}")
    return float(duration)


def get_voice_duration(path):
    return int(get_voice_duration_float(path))


def get_audio_duration(path):
    return get_voice_duration_float(path)


def get_duration(path):
    return get_voice_duration(path)


def get_duration_float(path):
    return get_voice_duration_float(path)


def safe_get_voice_duration(path, default=0.0):
    try:
        return get_voice_duration_float(path)
    except Exception:
        return float(default)


def classify_voice_duration(duration):
    duration = float(duration or 0.0)
    if duration <= 0:
        return "UNKNOWN"
    if duration <= SHORT_LIMIT_SECONDS:
        return "SHORT"
    if duration >= LONG_MIN_SECONDS:
        return "LONG"
    return "BORDERLINE"


def mode_from_voice_duration(duration):
    return "SHORT" if float(duration or 0.0) <= SHORT_LIMIT_SECONDS else "LONG"


def mode_from_voice_file(path):
    return mode_from_voice_duration(get_voice_duration_float(path))


def safe_short_duration(duration):
    return min(float(duration or 0.0), SHORT_SAFE_LIMIT_SECONDS)


def voice_duration_report(path):
    p = _validate_file(path, "voice")
    duration = get_voice_duration_float(p)
    data = ffprobe_json(p)
    streams = data.get("streams", [])
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    return {
        "path": str(p),
        "exists": p.exists(),
        "suffix": p.suffix.lower(),
        "duration": round(duration, 3),
        "duration_int": int(duration),
        "mode": mode_from_voice_duration(duration),
        "classification": classify_voice_duration(duration),
        "short_safe_duration": round(safe_short_duration(duration), 3),
        "audio_stream_count": len(audio_streams),
        "format": data.get("format", {}),
        "audio_streams": audio_streams,
    }


def batch_voice_duration_report(paths):
    reports = []
    total = 0.0
    for p in paths or []:
        try:
            r = voice_duration_report(p)
            reports.append(r)
            total += float(r["duration"])
        except Exception as e:
            reports.append({"path": str(p), "error": str(e), "duration": 0.0})
    return {
        "count": len(reports),
        "total_duration": round(total, 3),
        "mode_by_total": mode_from_voice_duration(total),
        "items": reports,
    }


def list_audio_files(folder):
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS], key=lambda p: p.name.lower())


def get_folder_voice_report(folder):
    files = list_audio_files(folder)
    return batch_voice_duration_report(files)


def build_concat_file(audio_files, output_txt=None):
    files = [_validate_file(p, "audio") for p in audio_files or []]
    if not files:
        raise ValueError("No audio files provided.")
    output_txt = Path(output_txt or OUTPUT_DIR / "voice_concat_list.txt")
    output_txt.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for f in files:
        safe_path = str(f.resolve()).replace("'", "'\\''")
        lines.append(f"file '{safe_path}'")
    output_txt.write_text("\n".join(lines), encoding="utf-8")
    return str(output_txt)


def merge_voice_files(audio_files, output_path=None, reencode=True):
    files = [_validate_file(p, "audio") for p in audio_files or []]
    if not files:
        raise ValueError("No audio files provided for merge.")
    output_path = Path(output_path or OUTPUT_DIR / "merged_voice.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_txt = build_concat_file(files, OUTPUT_DIR / "merge_list.txt")
    if reencode:
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s16le" if output_path.suffix.lower() == ".wav" else "aac",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-c", "copy",
            str(output_path),
        ]
    try:
        _run(cmd, label="merge_voice_files")
    except Exception:
        if not reencode:
            return merge_voice_files(files, output_path=output_path, reencode=True)
        raise
    return str(output_path)


def trim_audio_file(input_path, output_path=None, duration=None, start=0.0):
    p = _validate_file(input_path, "audio")
    if duration is None:
        duration = get_voice_duration_float(p)
    duration = max(float(duration), MIN_DURATION)
    start = max(float(start or 0.0), 0.0)
    output_path = Path(output_path or OUTPUT_DIR / f"{p.stem}_trimmed{p.suffix}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-i", str(p),
        "-t", str(duration),
        "-ar", "48000",
        "-ac", "2",
    ]
    if output_path.suffix.lower() == ".wav":
        cmd += ["-c:a", "pcm_s16le"]
    else:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += [str(output_path)]
    _run(cmd, label="trim_audio_file")
    return str(output_path)


def pad_audio_file(input_path, output_path=None, target_duration=None):
    p = _validate_file(input_path, "audio")
    current = get_voice_duration_float(p)
    target = float(target_duration if target_duration is not None else current)
    output_path = Path(output_path or OUTPUT_DIR / f"{p.stem}_padded{p.suffix}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if target <= current:
        return trim_audio_file(p, output_path=output_path, duration=target)
    pad = target - current
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(p),
        "-af", f"apad=pad_dur={pad}",
        "-t", str(target),
        "-ar", "48000",
        "-ac", "2",
    ]
    if output_path.suffix.lower() == ".wav":
        cmd += ["-c:a", "pcm_s16le"]
    else:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += [str(output_path)]
    _run(cmd, label="pad_audio_file")
    return str(output_path)


def fit_audio_to_duration(input_path, output_path=None, target_duration=None):
    p = _validate_file(input_path, "audio")
    current = get_voice_duration_float(p)
    target = float(target_duration if target_duration is not None else current)
    if current > target:
        return trim_audio_file(p, output_path=output_path, duration=target)
    if current < target:
        return pad_audio_file(p, output_path=output_path, target_duration=target)
    return str(p)


def compare_durations(primary, secondary, tolerance=0.15):
    a = get_voice_duration_float(primary)
    b = get_voice_duration_float(secondary)
    diff = a - b
    return {
        "primary": str(primary),
        "secondary": str(secondary),
        "primary_duration": round(a, 3),
        "secondary_duration": round(b, 3),
        "difference": round(diff, 3),
        "abs_difference": round(abs(diff), 3),
        "matches": abs(diff) <= float(tolerance),
        "tolerance": tolerance,
    }


def build_duration_guard_for_voice(voice_path, mode=None):
    duration = get_voice_duration_float(voice_path)
    resolved_mode = mode or mode_from_voice_duration(duration)
    export_duration = safe_short_duration(duration) if resolved_mode == "SHORT" else duration
    return {
        "voice_path": str(voice_path),
        "voice_duration": round(duration, 3),
        "mode": resolved_mode,
        "export_duration": round(export_duration, 3),
        "trim_required_for_short": resolved_mode == "SHORT" and export_duration < duration,
        "classification": classify_voice_duration(duration),
    }


def voice_timeline_from_files(audio_files):
    timeline = []
    cursor = 0.0
    for i, f in enumerate(audio_files or []):
        duration = safe_get_voice_duration(f, 0.0)
        timeline.append({
            "index": i,
            "path": str(f),
            "start": round(cursor, 3),
            "duration": round(duration, 3),
            "end": round(cursor + duration, 3),
        })
        cursor += duration
    return timeline


def validate_voice_files(audio_files):
    result = []
    for i, f in enumerate(audio_files or []):
        p = Path(f)
        item = {"index": i, "path": str(p), "exists": p.exists(), "suffix": p.suffix.lower()}
        if not p.exists():
            item["ok"] = False
            item["error"] = "missing"
        elif p.suffix.lower() not in AUDIO_EXTS:
            item["ok"] = False
            item["error"] = "unsupported_extension"
        else:
            try:
                item["duration"] = round(get_voice_duration_float(p), 3)
                item["ok"] = item["duration"] > MIN_DURATION
            except Exception as e:
                item["ok"] = False
                item["error"] = str(e)
        result.append(item)
    return {
        "ok": all(x.get("ok") for x in result) if result else False,
        "count": len(result),
        "items": result,
    }


def create_voice_manifest(audio_files, output_path=None):
    report = validate_voice_files(audio_files)
    timeline = voice_timeline_from_files(audio_files)
    manifest = {
        "validation": report,
        "timeline": timeline,
        "total_duration": round(sum(x["duration"] for x in timeline), 3),
        "mode": mode_from_voice_duration(sum(x["duration"] for x in timeline)),
    }
    path = Path(output_path or OUTPUT_DIR / "voice_manifest.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def read_voice_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def estimate_words_duration(text, words_per_minute=150):
    words = str(text or "").split()
    minutes = len(words) / max(1.0, float(words_per_minute))
    return minutes * 60.0


def expected_duration_from_words(words, words_per_second=2.5):
    count = len(words or [])
    return float(count) / max(0.1, float(words_per_second))


def duration_to_timestamp(seconds):
    seconds = float(seconds or 0.0)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def timestamp_to_duration(ts):
    parts = str(ts).strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except Exception:
        return 0.0


def split_duration_into_chunks(duration, chunk_size=8.0):
    duration = max(0.0, float(duration or 0.0))
    chunk_size = max(MIN_DURATION, float(chunk_size or 8.0))
    chunks = []
    cursor = 0.0
    index = 0
    while cursor < duration - 0.001:
        end = min(duration, cursor + chunk_size)
        chunks.append({
            "index": index,
            "start": round(cursor, 3),
            "end": round(end, 3),
            "duration": round(end - cursor, 3),
        })
        cursor = end
        index += 1
    return chunks


def voice_chunk_plan(voice_path, chunk_size=8.0):
    duration = get_voice_duration_float(voice_path)
    return {
        "voice_path": str(voice_path),
        "duration": round(duration, 3),
        "chunk_size": chunk_size,
        "chunks": split_duration_into_chunks(duration, chunk_size),
    }


def make_duration_filename(base="voice", duration=0.0, suffix=".wav"):
    safe_base = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(base))
    return f"{safe_base}_{duration_to_timestamp(duration).replace(':','-').replace('.','_')}{suffix}"


def save_duration_report(path, output_path=None):
    report = voice_duration_report(path)
    output_path = Path(output_path or OUTPUT_DIR / f"{Path(path).stem}_duration_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(output_path)


def project_voice_duration_summary(short_voice_dir=None, long_voice_dir=None):
    data = {}
    if short_voice_dir:
        data["short"] = get_folder_voice_report(short_voice_dir)
    if long_voice_dir:
        data["long"] = get_folder_voice_report(long_voice_dir)
    return data


def voice_duration_system_report():
    return {
        "output_dir": str(OUTPUT_DIR),
        "audio_exts": sorted(list(AUDIO_EXTS)),
        "video_exts": sorted(list(VIDEO_EXTS)),
        "short_limit_seconds": SHORT_LIMIT_SECONDS,
        "short_safe_limit_seconds": SHORT_SAFE_LIMIT_SECONDS,
        "long_min_seconds": LONG_MIN_SECONDS,
        "ffprobe_available": _ffprobe_available(),
    }


def _ffprobe_available():
    try:
        result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, shell=False)
        return result.returncode == 0
    except Exception:
        return False


def require_valid_voice(path):
    duration = get_voice_duration_float(path)
    if duration <= MIN_DURATION:
        raise RuntimeError(f"Voice duration too short: {duration}")
    return str(Path(path))


def require_short_voice(path):
    duration = get_voice_duration_float(path)
    if duration > SHORT_LIMIT_SECONDS:
        raise RuntimeError(f"Voice too long for short: {duration:.2f}s")
    return str(Path(path))


def require_long_voice(path):
    duration = get_voice_duration_float(path)
    if duration < LONG_MIN_SECONDS:
        safe_print(f"[VoiceDuration] Warning: voice is shorter than typical long video: {duration:.2f}s")
    return str(Path(path))


def get_voice_duration_int(path):
    return int(round(get_voice_duration_float(path)))


def get_voice_duration_ceil(path):
    return int(math.ceil(get_voice_duration_float(path)))


def get_voice_duration_floor(path):
    return int(math.floor(get_voice_duration_float(path)))


def format_duration_report(path):
    r = voice_duration_report(path)
    return (
        f"Voice: {r['path']}\n"
        f"Duration: {r['duration']}s\n"
        f"Mode: {r['mode']}\n"
        f"Classification: {r['classification']}"
    )


def print_voice_duration(path):
    text = format_duration_report(path)
    print(text)
    return text


def safe_duration_match(media_path, voice_path, tolerance=0.15):
    try:
        return compare_durations(media_path, voice_path, tolerance=tolerance)["matches"]
    except Exception:
        return False


def duration_difference(media_path, voice_path):
    return compare_durations(media_path, voice_path)["difference"]


def build_export_duration_plan(voice_path, target_mode=None):
    duration = get_voice_duration_float(voice_path)
    mode = target_mode or mode_from_voice_duration(duration)
    if mode == "SHORT":
        final_duration = safe_short_duration(duration)
    else:
        final_duration = duration
    return {
        "voice_path": str(voice_path),
        "voice_duration": round(duration, 3),
        "target_mode": mode,
        "final_duration": round(final_duration, 3),
        "needs_trim": final_duration < duration,
        "chunks_8s": split_duration_into_chunks(final_duration, 8.0),
    }


def load_duration_from_cache(cache_path):
    p = Path(cache_path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_duration_cache(path, cache_path=None):
    report = voice_duration_report(path)
    cache_path = Path(cache_path or OUTPUT_DIR / f"{Path(path).stem}.duration_cache.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(cache_path)


class VoiceDurationTool:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def duration(self, path):
        return get_voice_duration_float(path)

    def report(self, path):
        return voice_duration_report(path)

    def batch(self, paths):
        return batch_voice_duration_report(paths)

    def folder(self, folder):
        return get_folder_voice_report(folder)

    def merge(self, files, output_path=None):
        return merge_voice_files(files, output_path=output_path or self.output_dir / "merged_voice.wav")

    def trim(self, input_path, output_path=None, duration=None, start=0.0):
        return trim_audio_file(input_path, output_path=output_path, duration=duration, start=start)

    def fit(self, input_path, output_path=None, target_duration=None):
        return fit_audio_to_duration(input_path, output_path=output_path, target_duration=target_duration)

    def manifest(self, files, output_path=None):
        return create_voice_manifest(files, output_path=output_path or self.output_dir / "voice_manifest.json")

    def plan(self, voice_path, mode=None):
        return build_export_duration_plan(voice_path, target_mode=mode)


def legacy_get_voice_duration(path):
    return get_voice_duration(path)


def voice_len(path):
    return get_voice_duration_float(path)


def audio_len(path):
    return get_voice_duration_float(path)


def get_len(path):
    return get_voice_duration_float(path)


def duration_guard(path):
    return build_duration_guard_for_voice(path)


if __name__ == "__main__":
    print(json.dumps(voice_duration_system_report(), indent=2))

def _voice_duration_helper_1(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_2(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_3(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_4(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_5(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_6(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_7(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_8(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_9(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_10(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_11(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_12(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_13(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_14(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_15(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_16(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_17(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_18(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_19(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_20(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_21(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_22(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_23(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_24(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_25(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_26(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_27(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_28(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_29(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_30(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_31(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_32(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_33(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_34(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_35(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_36(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_37(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_38(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_39(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_40(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_41(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_42(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_43(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_44(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_45(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_46(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_47(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_48(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_49(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_50(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_51(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_52(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_53(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_54(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_55(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_56(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_57(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_58(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_59(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_60(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_61(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_62(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_63(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_64(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_65(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_66(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_67(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_68(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_69(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_70(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_71(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_72(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_73(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_74(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_75(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_76(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_77(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_78(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_79(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_80(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_81(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_82(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_83(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_84(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_85(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_86(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_87(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_88(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_89(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_90(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_91(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_92(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_93(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_94(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_95(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_96(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_97(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_98(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_99(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_100(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_101(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_102(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_103(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_104(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_105(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_106(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_107(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_108(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_109(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_110(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_111(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_112(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_113(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_114(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_115(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_116(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_117(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_118(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_119(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_120(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_121(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_122(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_123(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_124(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_125(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_126(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_127(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_128(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_129(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_130(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_131(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_132(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_133(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_134(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_135(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_136(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_137(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_138(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_139(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_140(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_141(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_142(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_143(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_144(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_145(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_146(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_147(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_148(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_149(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_150(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_151(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_152(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_153(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_154(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_155(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_156(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_157(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_158(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_159(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_160(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_161(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_162(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_163(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_164(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_165(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_166(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_167(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_168(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_169(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_170(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_171(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_172(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_173(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_174(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_175(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_176(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_177(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_178(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_179(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_180(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_181(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_182(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_183(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_184(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_185(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_186(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_187(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_188(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_189(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_190(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_191(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_192(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_193(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_194(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_195(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_196(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_197(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_198(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_199(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_200(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_201(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_202(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_203(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_204(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_205(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_206(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_207(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_208(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_209(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _voice_duration_helper_210(value=None):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


# --- AUTO-ADDED ALIASES FOR COMPATIBILITY ---
def get_voice_duration_report(path):
    if 'voice_duration_report' in globals():
        return voice_duration_report(path)
    return {}


# --- AUTO-PATCH: MISSING ALIASES ---
def get_voice_duration_report(path):
    if 'voice_duration_report' in globals():
        return voice_duration_report(path)
    return {}
