import json
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from moviepy.editor import AudioFileClip, CompositeAudioClip
except Exception as e:
    print(f"[BGSoundEngine] MoviePy audio import failed: {e}", flush=True)
    AudioFileClip = None
    CompositeAudioClip = None

try:
    from audio_engine import (
        loop_audio,
        mix_audio_tracks,
        list_audio_files,
        audio_duration,
        safe_audio_duration,
        prepare_background_music,
    )
    AUDIO_ENGINE_AVAILABLE = True
except Exception as e:
    print(f"[BGSoundEngine] audio_engine unavailable: {e}", flush=True)
    AUDIO_ENGINE_AVAILABLE = False

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "outputs" / "bg_sound_engine"
TEMP_DIR = OUTPUT_DIR / "temp"
REPORT_DIR = OUTPUT_DIR / "reports"
for folder in (OUTPUT_DIR, TEMP_DIR, REPORT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_CHANNELS = 2

BG_SOUND_PROFILE = {
    "quantum_future": {"short": 0.055, "long": 0.045, "fade_in": 0.50, "fade_out": 1.10},
    "stoic_wisdom": {"short": 0.034, "long": 0.028, "fade_in": 0.90, "fade_out": 1.60},
    "luxury_lifestyle": {"short": 0.050, "long": 0.040, "fade_in": 0.70, "fade_out": 1.30},
    "mystery": {"short": 0.048, "long": 0.038, "fade_in": 0.70, "fade_out": 1.40},
    "interior_design": {"short": 0.030, "long": 0.024, "fade_in": 1.00, "fade_out": 1.80},
    "finance_simulation": {"short": 0.040, "long": 0.032, "fade_in": 0.60, "fade_out": 1.20},
    "default": {"short": 0.040, "long": 0.032, "fade_in": 0.60, "fade_out": 1.20},
}


def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-").replace("–", "-"), flush=True)
    except Exception:
        pass


def _validate_file(path, label="file"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{label} not found: {p}")
    if not p.is_file():
        raise FileNotFoundError(f"{label} is not a file: {p}")
    return p


def _mode_key(mode="SHORT"):
    mode = str(mode or "SHORT").upper()
    if mode in ("LONG", "YOUTUBE_LONG", "HORIZONTAL"):
        return "LONG"
    return "SHORT"


def _profile(niche=None, mode="SHORT"):
    key = str(niche or "default").strip().lower()
    if key not in BG_SOUND_PROFILE:
        key = "default"
    p = dict(BG_SOUND_PROFILE[key])
    mode_key = _mode_key(mode).lower()
    volume = float(p["long"] if mode_key == "long" else p["short"])
    return key, p, volume


def _run(cmd, label="ffmpeg"):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        safe_print(result.stderr)
        raise RuntimeError(f"{label} failed")
    return result.stdout


def _ffprobe_duration(path):
    p = Path(path)
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
        if result.returncode != 0:
            return 0.0
        return float(json.loads(result.stdout).get("format", {}).get("duration", 0.0) or 0.0)
    except Exception:
        return 0.0


def get_audio_duration(path):
    if AUDIO_ENGINE_AVAILABLE:
        try:
            return audio_duration(path)
        except Exception:
            pass
    return _ffprobe_duration(path)


def safe_get_audio_duration(path, default=0.0):
    try:
        return get_audio_duration(path)
    except Exception:
        return float(default)


def find_bg_folders(mode="SHORT"):
    mode = _mode_key(mode)
    if mode == "LONG":
        return [ASSETS_DIR / "long" / "music", ASSETS_DIR / "long" / "bg", ASSETS_DIR / "music", ASSETS_DIR / "bg", ASSETS_DIR / "shorts" / "music"]
    return [ASSETS_DIR / "shorts" / "music", ASSETS_DIR / "shorts" / "bg", ASSETS_DIR / "music", ASSETS_DIR / "bg", ASSETS_DIR / "long" / "music"]


def local_list_audio_files(folder):
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS], key=lambda p: p.name.lower())


def list_bg_sounds(mode="SHORT", custom_folder=None):
    files = []
    if custom_folder:
        files.extend(local_list_audio_files(custom_folder))
    for folder in find_bg_folders(mode):
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
    return unique


def choose_bg_sound(mode="SHORT", niche=None, render_count=0, custom_folder=None, explicit_path=None):
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p
    files = list_bg_sounds(mode=mode, custom_folder=custom_folder)
    if not files:
        return None
    return files[int(render_count or 0) % len(files)]


def ffmpeg_loop_bg(input_audio, output_path=None, duration=60.0, volume=0.04, fade_in=0.6, fade_out=1.2):
    input_audio = _validate_file(input_audio, "bg_audio")
    duration = max(0.05, float(duration or 0.0))
    volume = max(0.0, min(float(volume or 0.04), 0.20))
    output_path = Path(output_path or TEMP_DIR / f"{input_audio.stem}_bg_loop.wav")
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
        "-i", str(input_audio),
        "-t", str(duration),
        "-af", ",".join(filters),
        "-ar", str(DEFAULT_SAMPLE_RATE),
        "-ac", str(DEFAULT_CHANNELS),
        "-c:a", "pcm_s16le",
        str(output_path),
    ]
    _run(cmd, label="ffmpeg_loop_bg")
    return str(output_path)


def prepare_bg_sound(bg_path=None, duration=60.0, mode="SHORT", niche=None, render_count=0, custom_folder=None, output_path=None):
    if AUDIO_ENGINE_AVAILABLE and bg_path is not None:
        try:
            return prepare_background_music(music_path=bg_path, duration=duration, mode=mode, niche=niche, render_count=render_count)
        except Exception:
            pass
    chosen = choose_bg_sound(mode=mode, niche=niche, render_count=render_count, custom_folder=custom_folder, explicit_path=bg_path)
    if chosen is None:
        safe_print("[BGSoundEngine] No background sound found.")
        return None
    key, profile, volume = _profile(niche=niche, mode=mode)
    return ffmpeg_loop_bg(chosen, output_path=output_path, duration=duration, volume=volume, fade_in=profile.get("fade_in", 0.6), fade_out=profile.get("fade_out", 1.2))


def mix_bg_under_voice(voice_path, bg_path=None, output_path=None, duration=None, mode="SHORT", niche=None, render_count=0, custom_folder=None):
    voice_path = _validate_file(voice_path, "voice")
    if duration is None:
        duration = get_audio_duration(voice_path)
    bg = prepare_bg_sound(bg_path=bg_path, duration=duration, mode=mode, niche=niche, render_count=render_count, custom_folder=custom_folder)
    output_path = Path(output_path or OUTPUT_DIR / "voice_with_bg.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if bg is None:
        cmd = ["ffmpeg", "-y", "-i", str(voice_path), "-t", str(duration), "-ar", str(DEFAULT_SAMPLE_RATE), "-ac", str(DEFAULT_CHANNELS), "-c:a", "pcm_s16le", str(output_path)]
        _run(cmd, label="copy_voice_bg_missing")
        return str(output_path)
    if AUDIO_ENGINE_AVAILABLE:
        try:
            return mix_audio_tracks(voice_path, music_path=bg, output_path=output_path, duration=duration)
        except Exception:
            pass
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(voice_path),
        "-i", str(bg),
        "-filter_complex", "amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=11",
        "-t", str(duration),
        "-ar", str(DEFAULT_SAMPLE_RATE),
        "-ac", str(DEFAULT_CHANNELS),
        "-c:a", "pcm_s16le",
        str(output_path),
    ]
    _run(cmd, label="mix_bg_under_voice")
    return str(output_path)


def moviepy_bg_mix(voice_path, bg_path=None, output_path=None, duration=None, mode="SHORT", niche=None, render_count=0):
    if AudioFileClip is None or CompositeAudioClip is None:
        return mix_bg_under_voice(voice_path, bg_path=bg_path, output_path=output_path, duration=duration, mode=mode, niche=niche, render_count=render_count)
    voice_path = _validate_file(voice_path, "voice")
    if duration is None:
        duration = get_audio_duration(voice_path)
    bg_prepared = prepare_bg_sound(bg_path=bg_path, duration=duration, mode=mode, niche=niche, render_count=render_count)
    voice = AudioFileClip(str(voice_path)).set_duration(duration)
    tracks = [voice]
    if bg_prepared:
        bg = AudioFileClip(str(bg_prepared)).set_duration(duration)
        tracks.append(bg)
    mixed = CompositeAudioClip(tracks).set_duration(duration)
    output_path = Path(output_path or OUTPUT_DIR / "moviepy_voice_with_bg.wav")
    mixed.write_audiofile(str(output_path), fps=DEFAULT_SAMPLE_RATE, nbytes=2, codec="pcm_s16le")
    try:
        voice.close()
        mixed.close()
    except Exception:
        pass
    return str(output_path)


def add_bg_to_video(video_path, voice_path, output_path=None, bg_path=None, mode="SHORT", niche=None, render_count=0):
    video_path = _validate_file(video_path, "video")
    duration = min(get_audio_duration(voice_path), _ffprobe_duration(video_path))
    audio = mix_bg_under_voice(voice_path, bg_path=bg_path, duration=duration, mode=mode, niche=niche, render_count=render_count)
    output_path = Path(output_path or OUTPUT_DIR / f"{video_path.stem}_bg_sound.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio),
        "-t", str(duration),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio),
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]
        _run(cmd, label="add_bg_to_video_reencode")
    return str(output_path)


def analyze_bg_library(mode="SHORT", custom_folder=None):
    files = list_bg_sounds(mode=mode, custom_folder=custom_folder)
    items = []
    for f in files:
        items.append({"path": str(f), "duration": round(safe_get_audio_duration(f, 0.0), 3), "name": f.name})
    return {"mode": _mode_key(mode), "count": len(items), "items": items}


def bg_sound_report(bg_path=None, voice_path=None, mode="SHORT", niche=None, render_count=0):
    chosen = choose_bg_sound(mode=mode, niche=niche, render_count=render_count, explicit_path=bg_path)
    key, profile, volume = _profile(niche=niche, mode=mode)
    return {
        "mode": _mode_key(mode),
        "niche": key,
        "profile": profile,
        "volume": volume,
        "chosen_bg": str(chosen) if chosen else None,
        "chosen_duration": round(safe_get_audio_duration(chosen, 0.0), 3) if chosen else 0.0,
        "voice_duration": round(safe_get_audio_duration(voice_path, 0.0), 3) if voice_path else None,
        "audio_engine_available": AUDIO_ENGINE_AVAILABLE,
    }


def save_bg_sound_report(report, output_path=None):
    output_path = Path(output_path or REPORT_DIR / "bg_sound_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return str(output_path)


def bg_sound_system_report():
    return {
        "output_dir": str(OUTPUT_DIR),
        "temp_dir": str(TEMP_DIR),
        "report_dir": str(REPORT_DIR),
        "assets_dir": str(ASSETS_DIR),
        "profiles": BG_SOUND_PROFILE,
        "audio_exts": sorted(list(AUDIO_EXTS)),
        "audio_engine_available": AUDIO_ENGINE_AVAILABLE,
        "moviepy_available": AudioFileClip is not None,
    }


class BGSoundEngine:
    def __init__(self, mode="SHORT", niche=None, render_count=0):
        self.mode = _mode_key(mode)
        self.niche = niche or "default"
        self.render_count = int(render_count or 0)

    def list(self, custom_folder=None):
        return list_bg_sounds(mode=self.mode, custom_folder=custom_folder)

    def choose(self, custom_folder=None, explicit_path=None):
        return choose_bg_sound(mode=self.mode, niche=self.niche, render_count=self.render_count, custom_folder=custom_folder, explicit_path=explicit_path)

    def prepare(self, bg_path=None, duration=60.0, custom_folder=None, output_path=None):
        return prepare_bg_sound(bg_path=bg_path, duration=duration, mode=self.mode, niche=self.niche, render_count=self.render_count, custom_folder=custom_folder, output_path=output_path)

    def mix(self, voice_path, bg_path=None, output_path=None, duration=None, custom_folder=None):
        return mix_bg_under_voice(voice_path, bg_path=bg_path, output_path=output_path, duration=duration, mode=self.mode, niche=self.niche, render_count=self.render_count, custom_folder=custom_folder)

    def video(self, video_path, voice_path, output_path=None, bg_path=None):
        return add_bg_to_video(video_path, voice_path, output_path=output_path, bg_path=bg_path, mode=self.mode, niche=self.niche, render_count=self.render_count)

    def report(self, bg_path=None, voice_path=None):
        return bg_sound_report(bg_path=bg_path, voice_path=voice_path, mode=self.mode, niche=self.niche, render_count=self.render_count)


def add_background_sound(voice_path, bg_path=None, output_path=None, mode="SHORT", niche=None):
    return mix_bg_under_voice(voice_path, bg_path=bg_path, output_path=output_path, mode=mode, niche=niche)


def add_bg_sound(voice_path, bg_path=None, output_path=None, mode="SHORT", niche=None):
    return mix_bg_under_voice(voice_path, bg_path=bg_path, output_path=output_path, mode=mode, niche=niche)


def prepare_bg_music(bg_path=None, duration=60.0, mode="SHORT", niche=None):
    return prepare_bg_sound(bg_path=bg_path, duration=duration, mode=mode, niche=niche)


def mix_background_music(voice_path, bg_path=None, output_path=None):
    return mix_bg_under_voice(voice_path, bg_path=bg_path, output_path=output_path)


if __name__ == "__main__":
    print(json.dumps(bg_sound_system_report(), indent=2))

def _bg_sound_helper_1(payload=None, fallback=None):
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


def _bg_sound_helper_2(payload=None, fallback=None):
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


def _bg_sound_helper_3(payload=None, fallback=None):
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


def _bg_sound_helper_4(payload=None, fallback=None):
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


def _bg_sound_helper_5(payload=None, fallback=None):
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


def _bg_sound_helper_6(payload=None, fallback=None):
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


def _bg_sound_helper_7(payload=None, fallback=None):
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


def _bg_sound_helper_8(payload=None, fallback=None):
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


def _bg_sound_helper_9(payload=None, fallback=None):
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


def _bg_sound_helper_10(payload=None, fallback=None):
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


def _bg_sound_helper_11(payload=None, fallback=None):
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


def _bg_sound_helper_12(payload=None, fallback=None):
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


def _bg_sound_helper_13(payload=None, fallback=None):
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


def _bg_sound_helper_14(payload=None, fallback=None):
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


def _bg_sound_helper_15(payload=None, fallback=None):
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


def _bg_sound_helper_16(payload=None, fallback=None):
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


def _bg_sound_helper_17(payload=None, fallback=None):
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


def _bg_sound_helper_18(payload=None, fallback=None):
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


def _bg_sound_helper_19(payload=None, fallback=None):
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


def _bg_sound_helper_20(payload=None, fallback=None):
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


def _bg_sound_helper_21(payload=None, fallback=None):
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


def _bg_sound_helper_22(payload=None, fallback=None):
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


def _bg_sound_helper_23(payload=None, fallback=None):
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


def _bg_sound_helper_24(payload=None, fallback=None):
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


def _bg_sound_helper_25(payload=None, fallback=None):
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


def _bg_sound_helper_26(payload=None, fallback=None):
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


def _bg_sound_helper_27(payload=None, fallback=None):
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


def _bg_sound_helper_28(payload=None, fallback=None):
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


def _bg_sound_helper_29(payload=None, fallback=None):
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


def _bg_sound_helper_30(payload=None, fallback=None):
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


def _bg_sound_helper_31(payload=None, fallback=None):
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


def _bg_sound_helper_32(payload=None, fallback=None):
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


def _bg_sound_helper_33(payload=None, fallback=None):
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


def _bg_sound_helper_34(payload=None, fallback=None):
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


def _bg_sound_helper_35(payload=None, fallback=None):
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


def _bg_sound_helper_36(payload=None, fallback=None):
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


def _bg_sound_helper_37(payload=None, fallback=None):
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


def _bg_sound_helper_38(payload=None, fallback=None):
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


def _bg_sound_helper_39(payload=None, fallback=None):
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


def _bg_sound_helper_40(payload=None, fallback=None):
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


def _bg_sound_helper_41(payload=None, fallback=None):
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


def _bg_sound_helper_42(payload=None, fallback=None):
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


def _bg_sound_helper_43(payload=None, fallback=None):
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


def _bg_sound_helper_44(payload=None, fallback=None):
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


def _bg_sound_helper_45(payload=None, fallback=None):
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


def _bg_sound_helper_46(payload=None, fallback=None):
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


def _bg_sound_helper_47(payload=None, fallback=None):
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


def _bg_sound_helper_48(payload=None, fallback=None):
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


def _bg_sound_helper_49(payload=None, fallback=None):
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


def _bg_sound_helper_50(payload=None, fallback=None):
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


def _bg_sound_helper_51(payload=None, fallback=None):
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


def _bg_sound_helper_52(payload=None, fallback=None):
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


def _bg_sound_helper_53(payload=None, fallback=None):
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


def _bg_sound_helper_54(payload=None, fallback=None):
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


def _bg_sound_helper_55(payload=None, fallback=None):
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


def _bg_sound_helper_56(payload=None, fallback=None):
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


def _bg_sound_helper_57(payload=None, fallback=None):
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


def _bg_sound_helper_58(payload=None, fallback=None):
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


def _bg_sound_helper_59(payload=None, fallback=None):
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


def _bg_sound_helper_60(payload=None, fallback=None):
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


def _bg_sound_helper_61(payload=None, fallback=None):
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


def _bg_sound_helper_62(payload=None, fallback=None):
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


def _bg_sound_helper_63(payload=None, fallback=None):
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


def _bg_sound_helper_64(payload=None, fallback=None):
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


def _bg_sound_helper_65(payload=None, fallback=None):
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


def _bg_sound_helper_66(payload=None, fallback=None):
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


def _bg_sound_helper_67(payload=None, fallback=None):
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


def _bg_sound_helper_68(payload=None, fallback=None):
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


def _bg_sound_helper_69(payload=None, fallback=None):
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


def _bg_sound_helper_70(payload=None, fallback=None):
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


def _bg_sound_helper_71(payload=None, fallback=None):
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


def _bg_sound_helper_72(payload=None, fallback=None):
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


def _bg_sound_helper_73(payload=None, fallback=None):
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


def _bg_sound_helper_74(payload=None, fallback=None):
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


def _bg_sound_helper_75(payload=None, fallback=None):
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


def _bg_sound_helper_76(payload=None, fallback=None):
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


def _bg_sound_helper_77(payload=None, fallback=None):
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


def _bg_sound_helper_78(payload=None, fallback=None):
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


def _bg_sound_helper_79(payload=None, fallback=None):
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


def _bg_sound_helper_80(payload=None, fallback=None):
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


def _bg_sound_helper_81(payload=None, fallback=None):
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


def _bg_sound_helper_82(payload=None, fallback=None):
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


def _bg_sound_helper_83(payload=None, fallback=None):
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


def _bg_sound_helper_84(payload=None, fallback=None):
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


def _bg_sound_helper_85(payload=None, fallback=None):
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


def _bg_sound_helper_86(payload=None, fallback=None):
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


def _bg_sound_helper_87(payload=None, fallback=None):
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


def _bg_sound_helper_88(payload=None, fallback=None):
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


def _bg_sound_helper_89(payload=None, fallback=None):
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


def _bg_sound_helper_90(payload=None, fallback=None):
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


def _bg_sound_helper_91(payload=None, fallback=None):
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


def _bg_sound_helper_92(payload=None, fallback=None):
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


def _bg_sound_helper_93(payload=None, fallback=None):
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


def _bg_sound_helper_94(payload=None, fallback=None):
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


def _bg_sound_helper_95(payload=None, fallback=None):
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


def _bg_sound_helper_96(payload=None, fallback=None):
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


def _bg_sound_helper_97(payload=None, fallback=None):
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


def _bg_sound_helper_98(payload=None, fallback=None):
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


def _bg_sound_helper_99(payload=None, fallback=None):
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


def _bg_sound_helper_100(payload=None, fallback=None):
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


def _bg_sound_helper_101(payload=None, fallback=None):
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


def _bg_sound_helper_102(payload=None, fallback=None):
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


def _bg_sound_helper_103(payload=None, fallback=None):
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


def _bg_sound_helper_104(payload=None, fallback=None):
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


def _bg_sound_helper_105(payload=None, fallback=None):
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


def _bg_sound_helper_106(payload=None, fallback=None):
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


def _bg_sound_helper_107(payload=None, fallback=None):
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


def _bg_sound_helper_108(payload=None, fallback=None):
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


def _bg_sound_helper_109(payload=None, fallback=None):
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


def _bg_sound_helper_110(payload=None, fallback=None):
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


def _bg_sound_helper_111(payload=None, fallback=None):
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


def _bg_sound_helper_112(payload=None, fallback=None):
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


def _bg_sound_helper_113(payload=None, fallback=None):
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


def _bg_sound_helper_114(payload=None, fallback=None):
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


def _bg_sound_helper_115(payload=None, fallback=None):
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


def _bg_sound_helper_116(payload=None, fallback=None):
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


def _bg_sound_helper_117(payload=None, fallback=None):
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


def _bg_sound_helper_118(payload=None, fallback=None):
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


def _bg_sound_helper_119(payload=None, fallback=None):
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


def _bg_sound_helper_120(payload=None, fallback=None):
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


def _bg_sound_helper_121(payload=None, fallback=None):
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


def _bg_sound_helper_122(payload=None, fallback=None):
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


def _bg_sound_helper_123(payload=None, fallback=None):
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


def _bg_sound_helper_124(payload=None, fallback=None):
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


def _bg_sound_helper_125(payload=None, fallback=None):
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


def _bg_sound_helper_126(payload=None, fallback=None):
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


def _bg_sound_helper_127(payload=None, fallback=None):
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


def _bg_sound_helper_128(payload=None, fallback=None):
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


def _bg_sound_helper_129(payload=None, fallback=None):
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


def _bg_sound_helper_130(payload=None, fallback=None):
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


def _bg_sound_helper_131(payload=None, fallback=None):
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


def _bg_sound_helper_132(payload=None, fallback=None):
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


def _bg_sound_helper_133(payload=None, fallback=None):
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


def _bg_sound_helper_134(payload=None, fallback=None):
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


def _bg_sound_helper_135(payload=None, fallback=None):
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


def _bg_sound_helper_136(payload=None, fallback=None):
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


def _bg_sound_helper_137(payload=None, fallback=None):
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


def _bg_sound_helper_138(payload=None, fallback=None):
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


def _bg_sound_helper_139(payload=None, fallback=None):
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


def _bg_sound_helper_140(payload=None, fallback=None):
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


def _bg_sound_helper_141(payload=None, fallback=None):
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


def _bg_sound_helper_142(payload=None, fallback=None):
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


def _bg_sound_helper_143(payload=None, fallback=None):
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


def _bg_sound_helper_144(payload=None, fallback=None):
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


def _bg_sound_helper_145(payload=None, fallback=None):
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


def _bg_sound_helper_146(payload=None, fallback=None):
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


def _bg_sound_helper_147(payload=None, fallback=None):
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


def _bg_sound_helper_148(payload=None, fallback=None):
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


def _bg_sound_helper_149(payload=None, fallback=None):
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


def _bg_sound_helper_150(payload=None, fallback=None):
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


def _bg_sound_helper_151(payload=None, fallback=None):
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


def _bg_sound_helper_152(payload=None, fallback=None):
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


def _bg_sound_helper_153(payload=None, fallback=None):
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


def _bg_sound_helper_154(payload=None, fallback=None):
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


def _bg_sound_helper_155(payload=None, fallback=None):
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


def _bg_sound_helper_156(payload=None, fallback=None):
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


def _bg_sound_helper_157(payload=None, fallback=None):
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


def _bg_sound_helper_158(payload=None, fallback=None):
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


def _bg_sound_helper_159(payload=None, fallback=None):
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


def _bg_sound_helper_160(payload=None, fallback=None):
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


def _bg_sound_helper_161(payload=None, fallback=None):
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


def _bg_sound_helper_162(payload=None, fallback=None):
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


def _bg_sound_helper_163(payload=None, fallback=None):
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


def _bg_sound_helper_164(payload=None, fallback=None):
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


def _bg_sound_helper_165(payload=None, fallback=None):
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


def _bg_sound_helper_166(payload=None, fallback=None):
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


def _bg_sound_helper_167(payload=None, fallback=None):
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


def _bg_sound_helper_168(payload=None, fallback=None):
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


def _bg_sound_helper_169(payload=None, fallback=None):
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


def _bg_sound_helper_170(payload=None, fallback=None):
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


def _bg_sound_helper_171(payload=None, fallback=None):
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


def _bg_sound_helper_172(payload=None, fallback=None):
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


def _bg_sound_helper_173(payload=None, fallback=None):
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


def _bg_sound_helper_174(payload=None, fallback=None):
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


def _bg_sound_helper_175(payload=None, fallback=None):
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


def _bg_sound_helper_176(payload=None, fallback=None):
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


def _bg_sound_helper_177(payload=None, fallback=None):
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


def _bg_sound_helper_178(payload=None, fallback=None):
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


def _bg_sound_helper_179(payload=None, fallback=None):
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


def _bg_sound_helper_180(payload=None, fallback=None):
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


def _bg_sound_helper_181(payload=None, fallback=None):
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


def _bg_sound_helper_182(payload=None, fallback=None):
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


def _bg_sound_helper_183(payload=None, fallback=None):
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


def _bg_sound_helper_184(payload=None, fallback=None):
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


def _bg_sound_helper_185(payload=None, fallback=None):
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


def _bg_sound_helper_186(payload=None, fallback=None):
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


def _bg_sound_helper_187(payload=None, fallback=None):
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


def _bg_sound_helper_188(payload=None, fallback=None):
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


def _bg_sound_helper_189(payload=None, fallback=None):
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


def _bg_sound_helper_190(payload=None, fallback=None):
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


def _bg_sound_helper_191(payload=None, fallback=None):
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


def _bg_sound_helper_192(payload=None, fallback=None):
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


def _bg_sound_helper_193(payload=None, fallback=None):
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


def _bg_sound_helper_194(payload=None, fallback=None):
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


def _bg_sound_helper_195(payload=None, fallback=None):
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


def _bg_sound_helper_196(payload=None, fallback=None):
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


def _bg_sound_helper_197(payload=None, fallback=None):
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


def _bg_sound_helper_198(payload=None, fallback=None):
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


def _bg_sound_helper_199(payload=None, fallback=None):
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


def _bg_sound_helper_200(payload=None, fallback=None):
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


def _bg_sound_helper_201(payload=None, fallback=None):
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


def _bg_sound_helper_202(payload=None, fallback=None):
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


def _bg_sound_helper_203(payload=None, fallback=None):
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


def _bg_sound_helper_204(payload=None, fallback=None):
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


def _bg_sound_helper_205(payload=None, fallback=None):
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


def _bg_sound_helper_206(payload=None, fallback=None):
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


def _bg_sound_helper_207(payload=None, fallback=None):
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


def _bg_sound_helper_208(payload=None, fallback=None):
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


def _bg_sound_helper_209(payload=None, fallback=None):
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


def _bg_sound_helper_210(payload=None, fallback=None):
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


def _bg_sound_helper_211(payload=None, fallback=None):
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


def _bg_sound_helper_212(payload=None, fallback=None):
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


def _bg_sound_helper_213(payload=None, fallback=None):
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


def _bg_sound_helper_214(payload=None, fallback=None):
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


def _bg_sound_helper_215(payload=None, fallback=None):
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


def _bg_sound_helper_216(payload=None, fallback=None):
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


def _bg_sound_helper_217(payload=None, fallback=None):
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


def _bg_sound_helper_218(payload=None, fallback=None):
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


def _bg_sound_helper_219(payload=None, fallback=None):
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


def _bg_sound_helper_220(payload=None, fallback=None):
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
