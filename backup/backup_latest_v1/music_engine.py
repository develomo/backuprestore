import json
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from audio_engine import (
        loop_audio,
        list_audio_files,
        audio_duration,
        safe_audio_duration,
        prepare_background_music,
    )
    AUDIO_ENGINE_AVAILABLE = True
except Exception as e:
    print(f"[MusicEngine] audio_engine unavailable: {e}", flush=True)
    AUDIO_ENGINE_AVAILABLE = False

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "outputs" / "music_engine"
TEMP_DIR = OUTPUT_DIR / "temp"
REPORT_DIR = OUTPUT_DIR / "reports"
for folder in (OUTPUT_DIR, TEMP_DIR, REPORT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_CHANNELS = 2

MUSIC_PROFILES = {
    "quantum_future": {"short_volume": 0.055, "long_volume": 0.045, "fade_in": 0.45, "fade_out": 1.10, "mood": "futuristic"},
    "stoic_wisdom": {"short_volume": 0.034, "long_volume": 0.028, "fade_in": 0.90, "fade_out": 1.80, "mood": "calm"},
    "luxury_lifestyle": {"short_volume": 0.050, "long_volume": 0.040, "fade_in": 0.70, "fade_out": 1.50, "mood": "premium"},
    "mystery": {"short_volume": 0.046, "long_volume": 0.038, "fade_in": 0.75, "fade_out": 1.60, "mood": "suspense"},
    "interior_design": {"short_volume": 0.030, "long_volume": 0.024, "fade_in": 1.00, "fade_out": 2.00, "mood": "soft"},
    "finance_simulation": {"short_volume": 0.038, "long_volume": 0.032, "fade_in": 0.60, "fade_out": 1.30, "mood": "business"},
    "default": {"short_volume": 0.040, "long_volume": 0.032, "fade_in": 0.60, "fade_out": 1.20, "mood": "clean"},
}


def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-").replace("–", "-"), flush=True)
    except Exception:
        pass


def _mode_key(mode="SHORT"):
    mode = str(mode or "SHORT").upper()
    return "LONG" if mode in ("LONG", "YOUTUBE_LONG", "HORIZONTAL") else "SHORT"


def _resolve_niche(niche=None):
    key = str(niche or "default").strip().lower()
    return key if key in MUSIC_PROFILES else "default"


def _profile(niche=None, mode="SHORT"):
    key = _resolve_niche(niche)
    p = dict(MUSIC_PROFILES[key])
    p["niche"] = key
    p["mode"] = _mode_key(mode)
    p["volume"] = p["long_volume"] if p["mode"] == "LONG" else p["short_volume"]
    return p


def _validate_file(path, label="file"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{label} not found: {p}")
    if not p.is_file():
        raise FileNotFoundError(f"{label} is not a file: {p}")
    return p


def _run(cmd, label="ffmpeg"):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        safe_print(result.stderr)
        raise RuntimeError(f"{label} failed")
    return result.stdout


def ffprobe_duration(path):
    p = Path(path)
    if not p.exists():
        return 0.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
        if result.returncode != 0:
            return 0.0
        return float(json.loads(result.stdout).get("format", {}).get("duration", 0.0) or 0.0)
    except Exception:
        return 0.0


def get_music_duration(path):
    if AUDIO_ENGINE_AVAILABLE:
        try:
            return audio_duration(path)
        except Exception:
            pass
    return ffprobe_duration(path)


def safe_get_music_duration(path, default=0.0):
    try:
        return get_music_duration(path)
    except Exception:
        return float(default)


def local_list_audio_files(folder):
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS], key=lambda p: p.name.lower())


def music_folders(mode="SHORT", niche=None):
    mode = _mode_key(mode)
    key = _resolve_niche(niche)
    folders = []
    if mode == "LONG":
        folders += [ASSETS_DIR / "long" / "music", ASSETS_DIR / "long" / "bg"]
    else:
        folders += [ASSETS_DIR / "shorts" / "music", ASSETS_DIR / "shorts" / "bg"]
    folders += [
        ASSETS_DIR / "music" / key,
        ASSETS_DIR / "music",
        ASSETS_DIR / "bg",
    ]
    return folders


def list_music_files(mode="SHORT", niche=None, custom_folder=None):
    folders = []
    if custom_folder:
        folders.append(Path(custom_folder))
    folders.extend(music_folders(mode=mode, niche=niche))
    files = []
    for folder in folders:
        if AUDIO_ENGINE_AVAILABLE:
            try:
                files.extend(list_audio_files(folder))
            except Exception:
                files.extend(local_list_audio_files(folder))
        else:
            files.extend(local_list_audio_files(folder))
    seen = set()
    unique = []
    for f in files:
        key = str(Path(f).resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(Path(f))
    return sorted(unique, key=lambda p: p.name.lower())


def score_music_file(path, niche=None):
    p = Path(path)
    name = p.stem.lower()
    profile = _profile(niche=niche)
    score = 1.0
    mood = profile.get("mood", "")
    if mood and mood in name:
        score += 1.2
    if profile["niche"] in name:
        score += 1.5
    for word in str(profile.get("mood", "")).split("_"):
        if word and word in name:
            score += 0.5
    duration = safe_get_music_duration(p, 0.0)
    if duration >= 60:
        score += 0.5
    if duration >= 180:
        score += 0.4
    return score


def choose_music(mode="SHORT", niche=None, render_count=0, custom_folder=None, explicit_path=None):
    if explicit_path and Path(explicit_path).exists():
        return Path(explicit_path)
    files = list_music_files(mode=mode, niche=niche, custom_folder=custom_folder)
    if not files:
        return None
    ranked = sorted(files, key=lambda p: (-score_music_file(p, niche=niche), p.name.lower()))
    if int(render_count or 0) == 0:
        return ranked[0]
    return ranked[int(render_count or 0) % len(ranked)]


def ffmpeg_loop_music(input_music, output_path=None, duration=60.0, volume=0.04, fade_in=0.6, fade_out=1.2):
    input_music = _validate_file(input_music, "music")
    duration = max(0.05, float(duration or 0.0))
    volume = max(0.0, min(float(volume or 0.04), 0.20))
    output_path = Path(output_path or TEMP_DIR / f"{input_music.stem}_music_loop.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filters = [f"volume={volume}"]
    if fade_in > 0:
        filters.append(f"afade=t=in:st=0:d={float(fade_in)}")
    if fade_out > 0:
        filters.append(f"afade=t=out:st={max(0.0, duration - float(fade_out))}:d={float(fade_out)}")
    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", str(input_music),
        "-t", str(duration),
        "-af", ",".join(filters),
        "-ar", str(DEFAULT_SAMPLE_RATE),
        "-ac", str(DEFAULT_CHANNELS),
        "-c:a", "pcm_s16le",
        str(output_path),
    ]
    _run(cmd, label="ffmpeg_loop_music")
    return str(output_path)


def prepare_music_track(music_path=None, duration=60.0, mode="SHORT", niche=None, render_count=0, custom_folder=None, output_path=None, volume=None):
    chosen = choose_music(mode=mode, niche=niche, render_count=render_count, custom_folder=custom_folder, explicit_path=music_path)
    if chosen is None:
        safe_print("[MusicEngine] No music found.")
        return None
    profile = _profile(niche=niche, mode=mode)
    volume = profile["volume"] if volume is None else float(volume)
    if AUDIO_ENGINE_AVAILABLE:
        try:
            return prepare_background_music(music_path=chosen, duration=duration, mode=mode, niche=niche, render_count=render_count)
        except Exception:
            pass
    return ffmpeg_loop_music(chosen, output_path=output_path, duration=duration, volume=volume, fade_in=profile["fade_in"], fade_out=profile["fade_out"])


def trim_music(input_music, output_path=None, duration=60.0, start=0.0, volume=1.0):
    input_music = _validate_file(input_music, "music")
    output_path = Path(output_path or TEMP_DIR / f"{input_music.stem}_trim.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(max(0.0, float(start or 0.0))),
        "-i", str(input_music),
        "-t", str(max(0.05, float(duration))),
        "-af", f"volume={max(0.0, min(float(volume), 2.0))}",
        "-ar", str(DEFAULT_SAMPLE_RATE),
        "-ac", str(DEFAULT_CHANNELS),
        "-c:a", "pcm_s16le",
        str(output_path),
    ]
    _run(cmd, label="trim_music")
    return str(output_path)


def build_music_plan(duration=60.0, mode="SHORT", niche=None, render_count=0, custom_folder=None, explicit_path=None):
    chosen = choose_music(mode=mode, niche=niche, render_count=render_count, custom_folder=custom_folder, explicit_path=explicit_path)
    profile = _profile(niche=niche, mode=mode)
    return {
        "duration": round(float(duration or 0.0), 3),
        "mode": profile["mode"],
        "niche": profile["niche"],
        "profile": profile,
        "chosen_music": str(chosen) if chosen else None,
        "chosen_duration": round(safe_get_music_duration(chosen, 0.0), 3) if chosen else 0.0,
        "volume": profile["volume"],
        "fade_in": profile["fade_in"],
        "fade_out": profile["fade_out"],
    }


def analyze_music_library(mode="SHORT", niche=None, custom_folder=None):
    files = list_music_files(mode=mode, niche=niche, custom_folder=custom_folder)
    items = []
    for f in files:
        items.append({
            "path": str(f),
            "name": f.name,
            "duration": round(safe_get_music_duration(f, 0.0), 3),
            "score": round(score_music_file(f, niche=niche), 3),
        })
    items.sort(key=lambda x: (-x["score"], x["name"].lower()))
    return {"mode": _mode_key(mode), "niche": _resolve_niche(niche), "count": len(items), "items": items}


def save_music_plan(plan, output_path=None):
    output_path = Path(output_path or REPORT_DIR / "music_plan.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(output_path)


def music_engine_report(mode="SHORT", niche=None, render_count=0):
    return {
        "output_dir": str(OUTPUT_DIR),
        "temp_dir": str(TEMP_DIR),
        "profiles": MUSIC_PROFILES,
        "plan": build_music_plan(duration=60, mode=mode, niche=niche, render_count=render_count),
        "library": analyze_music_library(mode=mode, niche=niche),
        "audio_engine_available": AUDIO_ENGINE_AVAILABLE,
    }


class MusicEngine:
    def __init__(self, mode="SHORT", niche=None, render_count=0):
        self.mode = _mode_key(mode)
        self.niche = niche or "default"
        self.render_count = int(render_count or 0)

    def list(self, custom_folder=None):
        return list_music_files(mode=self.mode, niche=self.niche, custom_folder=custom_folder)

    def choose(self, custom_folder=None, explicit_path=None):
        return choose_music(mode=self.mode, niche=self.niche, render_count=self.render_count, custom_folder=custom_folder, explicit_path=explicit_path)

    def prepare(self, music_path=None, duration=60.0, custom_folder=None, output_path=None, volume=None):
        return prepare_music_track(music_path=music_path, duration=duration, mode=self.mode, niche=self.niche, render_count=self.render_count, custom_folder=custom_folder, output_path=output_path, volume=volume)

    def plan(self, duration=60.0, custom_folder=None, explicit_path=None):
        return build_music_plan(duration=duration, mode=self.mode, niche=self.niche, render_count=self.render_count, custom_folder=custom_folder, explicit_path=explicit_path)

    def library(self, custom_folder=None):
        return analyze_music_library(mode=self.mode, niche=self.niche, custom_folder=custom_folder)

    def report(self):
        return music_engine_report(mode=self.mode, niche=self.niche, render_count=self.render_count)


def prepare_bg_music(music_path=None, duration=60.0, mode="SHORT", niche=None):
    return prepare_music_track(music_path=music_path, duration=duration, mode=mode, niche=niche)


def prepare_music(music_path=None, duration=60.0, mode="SHORT", niche=None):
    return prepare_music_track(music_path=music_path, duration=duration, mode=mode, niche=niche)


def choose_bg_music(mode="SHORT", niche=None):
    return choose_music(mode=mode, niche=niche)


if __name__ == "__main__":
    print(json.dumps(music_engine_report(), indent=2))

def _music_engine_helper_1(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_2(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_3(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_4(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_5(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_6(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_7(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_8(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_9(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_10(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_11(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_12(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_13(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_14(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_15(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_16(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_17(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_18(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_19(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_20(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_21(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_22(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_23(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_24(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_25(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_26(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_27(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_28(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_29(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_30(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_31(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_32(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_33(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_34(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_35(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_36(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_37(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_38(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_39(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_40(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_41(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_42(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_43(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_44(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_45(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_46(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_47(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_48(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_49(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_50(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_51(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_52(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_53(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_54(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_55(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_56(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_57(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_58(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_59(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_60(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_61(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_62(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_63(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_64(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_65(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_66(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_67(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_68(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_69(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_70(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_71(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_72(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_73(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_74(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_75(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_76(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_77(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_78(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_79(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_80(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_81(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_82(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_83(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_84(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_85(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_86(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_87(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_88(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_89(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_90(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_91(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_92(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_93(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_94(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_95(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_96(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_97(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_98(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_99(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_100(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_101(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_102(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_103(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_104(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_105(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_106(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_107(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_108(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_109(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_110(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_111(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_112(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_113(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_114(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_115(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_116(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_117(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_118(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_119(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_120(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_121(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_122(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_123(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_124(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_125(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_126(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_127(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_128(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_129(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_130(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_131(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_132(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_133(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_134(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_135(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_136(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_137(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_138(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_139(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_140(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_141(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_142(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_143(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_144(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_145(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_146(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_147(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_148(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_149(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_150(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_151(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_152(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_153(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_154(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_155(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_156(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_157(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_158(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_159(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_160(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_161(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_162(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_163(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_164(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_165(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_166(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_167(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_168(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_169(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_170(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_171(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_172(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_173(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_174(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_175(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_176(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_177(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_178(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_179(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_180(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_181(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_182(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_183(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_184(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_185(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_186(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_187(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_188(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_189(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_190(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_191(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_192(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_193(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_194(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_195(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_196(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_197(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_198(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_199(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_200(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_201(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_202(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_203(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_204(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_205(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_206(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_207(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_208(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_209(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_210(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_211(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_212(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_213(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_214(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_215(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_216(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_217(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_218(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_219(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def _music_engine_helper_220(payload=None, fallback=None):
    if payload is None:
        return fallback
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, tuple):
        return tuple(payload)
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload
