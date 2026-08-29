"""
Professional Voice Humanization Engine
======================================

Drop-in local voice processor for My Creation Video Generator.

What it does:
- Uses 6 niche voice profiles + one Auto profile.
- Removes dead silence / robotic gaps when enabled.
- Applies niche EQ, compression, de-esser, saturation-style warmth,
  subtle room depth, loudness normalization and limiter.
- Keeps everything local/free using FFmpeg.
- Designed for both Shorts and Long video pipelines.

Files:
    config/voice_settings.json  -> UI settings
    outputs/voice_engine/       -> processed voices + reports
"""

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "outputs" / "voice_engine"

VOICE_SETTINGS_FILE = CONFIG_DIR / "voice_settings.json"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


VOICE_PROFILES = {
    "quantum_future": {
        "label": "Quantum Future",
        "keywords": ["ai", "future", "technology", "machine", "system", "robot", "digital", "automation"],
        "speed": 0.92,
        "volume": 1.07,
        "hpf": 80,
        "lpf": 12500,
        "warmth_freq": 140,
        "warmth_gain": 2.0,
        "mud_freq": 300,
        "mud_gain": -2.0,
        "presence_freq": 4000,
        "presence_gain": 2.0,
        "air_freq": 10000,
        "air_gain": 1.0,
        "compress_ratio": 2.5,
        "compress_threshold": -20,
        "deess_freq": 6500,
        "deess_gain": -3.0,
        "reverb_delay": 65,
        "reverb_decay": 0.08,
        "music_db": -27,
        "target_lufs": -16,
        "description": "Calm cinematic future-documentary voice."
    },
    "stoic_wisdom": {
        "label": "Stoic Wisdom",
        "keywords": ["wisdom", "discipline", "patience", "ego", "peace", "strength", "mind", "life"],
        "speed": 0.89,
        "volume": 1.05,
        "hpf": 75,
        "lpf": 12000,
        "warmth_freq": 150,
        "warmth_gain": 2.0,
        "mud_freq": 300,
        "mud_gain": -2.0,
        "presence_freq": 3500,
        "presence_gain": 1.5,
        "air_freq": 9000,
        "air_gain": 1.0,
        "compress_ratio": 2.0,
        "compress_threshold": -22,
        "deess_freq": 6200,
        "deess_gain": -2.5,
        "reverb_delay": 55,
        "reverb_decay": 0.06,
        "music_db": -29,
        "target_lufs": -16,
        "description": "Slow, wise, calm and reflective."
    },
    "luxury_lifestyle": {
        "label": "Luxury Lifestyle",
        "keywords": ["luxury", "wealth", "premium", "exclusive", "freedom", "elegance", "villa", "rich"],
        "speed": 0.93,
        "volume": 1.06,
        "hpf": 80,
        "lpf": 13000,
        "warmth_freq": 150,
        "warmth_gain": 2.0,
        "mud_freq": 300,
        "mud_gain": -2.0,
        "presence_freq": 3500,
        "presence_gain": 2.0,
        "air_freq": 11000,
        "air_gain": 2.0,
        "compress_ratio": 2.5,
        "compress_threshold": -20,
        "deess_freq": 6500,
        "deess_gain": -3.0,
        "reverb_delay": 70,
        "reverb_decay": 0.08,
        "music_db": -28,
        "target_lufs": -16,
        "description": "Smooth premium high-status narration."
    },
    "mystery": {
        "label": "Mystery",
        "keywords": ["secret", "hidden", "unknown", "truth", "evidence", "strange", "disappeared", "mystery"],
        "speed": 0.91,
        "volume": 1.06,
        "hpf": 80,
        "lpf": 12000,
        "warmth_freq": 140,
        "warmth_gain": 1.5,
        "mud_freq": 300,
        "mud_gain": -2.0,
        "presence_freq": 4000,
        "presence_gain": 2.0,
        "air_freq": 9000,
        "air_gain": 1.0,
        "compress_ratio": 2.5,
        "compress_threshold": -20,
        "deess_freq": 6500,
        "deess_gain": -3.0,
        "reverb_delay": 80,
        "reverb_decay": 0.09,
        "music_db": -30,
        "target_lufs": -16,
        "description": "Controlled suspense documentary narration."
    },
    "interior_design": {
        "label": "Interior Design",
        "keywords": ["interior", "design", "home", "room", "comfort", "warmth", "texture", "harmony"],
        "speed": 0.91,
        "volume": 1.04,
        "hpf": 75,
        "lpf": 13000,
        "warmth_freq": 150,
        "warmth_gain": 2.0,
        "mud_freq": 300,
        "mud_gain": -1.5,
        "presence_freq": 3500,
        "presence_gain": 1.5,
        "air_freq": 10000,
        "air_gain": 1.5,
        "compress_ratio": 2.0,
        "compress_threshold": -22,
        "deess_freq": 6000,
        "deess_gain": -2.5,
        "reverb_delay": 60,
        "reverb_decay": 0.07,
        "music_db": -28,
        "target_lufs": -16,
        "description": "Warm, soft, calm and aesthetic."
    },
    "finance_simulation": {
        "label": "Finance Simulation",
        "keywords": ["finance", "market", "inflation", "debt", "capital", "risk", "money", "wealth"],
        "speed": 0.95,
        "volume": 1.05,
        "hpf": 80,
        "lpf": 12500,
        "warmth_freq": 150,
        "warmth_gain": 1.5,
        "mud_freq": 300,
        "mud_gain": -2.0,
        "presence_freq": 4000,
        "presence_gain": 2.0,
        "air_freq": 10000,
        "air_gain": 1.0,
        "compress_ratio": 2.5,
        "compress_threshold": -20,
        "deess_freq": 6500,
        "deess_gain": -3.0,
        "reverb_delay": 45,
        "reverb_decay": 0.04,
        "music_db": -30,
        "target_lufs": -16,
        "description": "Analytical, strategic, trustworthy finance voice."
    },
}


DEFAULT_SETTINGS = {
    "voice_humanization_enabled": True,
    "voice_profile": "auto",
    "voice_strength": "balanced",
    "apply_to_short": True,
    "apply_to_long": True,
    "silence_cleanup": True,
    "voice_polish": True,
    "eq_enabled": True,
    "compression_enabled": True,
    "deesser_enabled": True,
    "reverb_enabled": True,
    "limiter_enabled": True,
    "loudnorm_enabled": True,
    "content_hint": ""
}


def load_voice_settings():
    if VOICE_SETTINGS_FILE.exists():
        try:
            data = json.loads(VOICE_SETTINGS_FILE.read_text(encoding="utf-8"))
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_voice_settings(settings):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    merged = DEFAULT_SETTINGS.copy()
    merged.update(settings or {})
    VOICE_SETTINGS_FILE.write_text(json.dumps(merged, indent=4), encoding="utf-8")
    return merged


def _read_text_file(path):
    try:
        p = Path(path)
        return p.read_text(encoding="utf-8").strip() if p.exists() else ""
    except Exception:
        return ""


def resolve_profile(profile="auto", content_hint="", niche_file=None):
    profile = (profile or "auto").strip().lower()

    if profile in VOICE_PROFILES:
        return profile

    hint = f"{content_hint or ''} {_read_text_file(niche_file) if niche_file else ''}".lower()

    scores = {}
    for key, data in VOICE_PROFILES.items():
        score = 0
        for kw in data.get("keywords", []):
            if kw in hint:
                score += 2
        if key in hint:
            score += 5
        scores[key] = score

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best

    niche = _read_text_file(niche_file).lower() if niche_file else ""
    if niche in VOICE_PROFILES:
        return niche

    return "quantum_future"


def _find_ffmpeg():
    local = BASE_DIR / "venv" / "Lib" / "site-packages" / "imageio_ffmpeg" / "binaries"
    if local.exists():
        exe_files = sorted(local.glob("ffmpeg*.exe"))
        if exe_files:
            return str(exe_files[0])
    found = shutil.which("ffmpeg")
    return found or "ffmpeg"


def _tempo_filter(speed):
    speed = max(0.50, min(2.00, float(speed or 1.0)))
    filters = []
    while speed > 2.0:
        filters.append("atempo=2.0")
        speed /= 2.0
    while speed < 0.5:
        filters.append("atempo=0.5")
        speed /= 0.5
    filters.append(f"atempo={speed:.3f}")
    return filters


def build_audio_filters(profile_id, settings):
    data = VOICE_PROFILES.get(profile_id, VOICE_PROFILES["quantum_future"])
    strength = str(settings.get("voice_strength", "balanced")).lower()

    if strength == "light":
        strength_mult = 0.70
    elif strength == "heavy":
        strength_mult = 1.20
    else:
        strength_mult = 1.00

    filters = []

    if settings.get("silence_cleanup", True):
        filters.append("silenceremove=start_periods=1:start_duration=0.18:start_threshold=-48dB:stop_periods=-1:stop_duration=0.35:stop_threshold=-48dB")

    filters.extend(_tempo_filter(data["speed"]))

    if settings.get("eq_enabled", True):
        filters.append(f"highpass=f={data['hpf']}")
        filters.append(f"lowpass=f={data['lpf']}")
        filters.append(f"equalizer=f={data['warmth_freq']}:t=q:w=1.0:g={data['warmth_gain'] * strength_mult:.2f}")
        filters.append(f"equalizer=f={data['mud_freq']}:t=q:w=1.0:g={data['mud_gain'] * strength_mult:.2f}")
        filters.append(f"equalizer=f={data['presence_freq']}:t=q:w=1.0:g={data['presence_gain'] * strength_mult:.2f}")
        filters.append(f"equalizer=f={data['air_freq']}:t=q:w=1.0:g={data['air_gain'] * strength_mult:.2f}")

    if settings.get("compression_enabled", True):
        filters.append(
            f"acompressor=threshold={data['compress_threshold']}dB:"
            f"ratio={data['compress_ratio']}:attack=20:release=120:makeup=1"
        )

    if settings.get("deesser_enabled", True):
        filters.append(f"equalizer=f={data['deess_freq']}:t=q:w=2.0:g={data['deess_gain'] * strength_mult:.2f}")

    filters.append(f"volume={data['volume']:.3f}")

    if settings.get("reverb_enabled", True):
        filters.append(f"aecho=0.8:0.12:{data['reverb_delay']}:{data['reverb_decay']:.3f}")

    if settings.get("loudnorm_enabled", True):
        filters.append(f"loudnorm=I={data['target_lufs']}:TP=-1.0:LRA=11")

    if settings.get("limiter_enabled", True):
        filters.append("alimiter=limit=0.8913")

    return ",".join(filters)


def humanize_voice_file(input_audio, mode="short", selected_profile=None, content_hint="", force=False):
    settings = load_voice_settings()

    if not settings.get("voice_humanization_enabled", True):
        print("[VoiceEngine] Humanization disabled. Using original voice.", flush=True)
        return str(input_audio)

    if mode == "short" and not settings.get("apply_to_short", True):
        print("[VoiceEngine] Short humanization disabled. Using original voice.", flush=True)
        return str(input_audio)

    if mode == "long" and not settings.get("apply_to_long", True):
        print("[VoiceEngine] Long humanization disabled. Using original voice.", flush=True)
        return str(input_audio)

    input_audio = Path(input_audio)
    if not input_audio.exists():
        raise FileNotFoundError(f"Voice file not found: {input_audio}")

    niche_file = CONFIG_DIR / "niche_settings.txt"
    profile_input = selected_profile or settings.get("voice_profile", "auto")
    profile_id = resolve_profile(profile_input, f"{settings.get('content_hint','')} {content_hint}", niche_file=niche_file)
    profile = VOICE_PROFILES[profile_id]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"humanized_{mode}_{profile_id}_{timestamp}.mp3"
    out_path = OUTPUT_DIR / out_name

    audio_filter = build_audio_filters(profile_id, settings)
    ffmpeg = _find_ffmpeg()

    cmd = [
        ffmpeg,
        "-y",
        "-i", str(input_audio),
        "-vn",
        "-af", audio_filter,
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "192k",
        str(out_path)
    ]

    print("", flush=True)
    print("========================================", flush=True)
    print("[VoiceEngine] PROFESSIONAL VOICE HUMANIZATION ACTIVE", flush=True)
    print("========================================", flush=True)
    print(f"Mode        : {mode}", flush=True)
    print(f"Input       : {input_audio}", flush=True)
    print(f"Output      : {out_path}", flush=True)
    print(f"Profile     : {profile_id} ({profile['label']})", flush=True)
    print(f"Strength    : {settings.get('voice_strength')}", flush=True)
    print(f"Silence cut : {settings.get('silence_cleanup')}", flush=True)
    print(f"Description : {profile['description']}", flush=True)
    print("========================================", flush=True)

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0 or not out_path.exists():
            print("[VoiceEngine] FFmpeg voice processing failed. Using original voice.", flush=True)
            print(result.stderr[-2000:], flush=True)
            return str(input_audio)
    except Exception as e:
        print(f"[VoiceEngine] Voice processing exception: {e}. Using original voice.", flush=True)
        return str(input_audio)

    report = {
        "created_at": datetime.now().isoformat(),
        "mode": mode,
        "input_audio": str(input_audio),
        "output_audio": str(out_path),
        "profile_id": profile_id,
        "profile_label": profile["label"],
        "settings": settings,
        "filter": audio_filter,
    }
    report_path = OUTPUT_DIR / f"voice_report_{mode}_{profile_id}_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=4), encoding="utf-8")

    print(f"[VoiceEngine] Saved humanized voice: {out_path}", flush=True)
    return str(out_path)


if __name__ == "__main__":
    save_voice_settings(DEFAULT_SETTINGS)
    print("Voice settings saved:", VOICE_SETTINGS_FILE)
    print("Available profiles:", ", ".join(["auto"] + list(VOICE_PROFILES.keys())))
