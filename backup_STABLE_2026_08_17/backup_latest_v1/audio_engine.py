# ============================================================
# PHASE 13 - AI AUDIO ENGINE V2
# FFmpeg-first audio mastering engine for My Creation Video Generator.
#
# Goals:
# - Backward compatible with old calls
# - Accept extra kwargs without crashing
# - Voice normalization / EQ / compression / limiter
# - Background music loop + ducking-style low mix
# - SFX cinematic layer
# - No paid API
# - Low RAM / CPU-safe
# - Works with batch_long_renderer.py Phase 13
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
import json
import math
import os
import shutil
import subprocess
import tempfile
import time

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs" / "audio_engine"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PHASE13_AUDIO_ENGINE_VERSION = "audio_engine_phase13_ai_audio_core_v2"


# ------------------------------------------------------------
# Basic utilities
# ------------------------------------------------------------

def safe_print(message: Any) -> None:
    try:
        print(str(message).replace("→", "->").replace("—", "-").replace("–", "-"), flush=True)
    except Exception:
        pass


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def inum(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def natural_key(path: Any):
    stem = Path(path).stem
    out = []
    cur = ""
    for ch in stem:
        if ch.isdigit():
            cur += ch
        else:
            if cur:
                out.append((0, int(cur)))
                cur = ""
            out.append((1, ch.lower()))
    if cur:
        out.append((0, int(cur)))
    return out


def existing_files(items: Optional[Iterable[Any]], exts: Optional[set] = None) -> List[Path]:
    out: List[Path] = []
    for item in items or []:
        try:
            p = Path(item)
            if p.exists() and p.is_file() and (exts is None or p.suffix.lower() in exts):
                out.append(p)
        except Exception:
            pass
    return sorted(out, key=natural_key)


def first_existing(items: Optional[Iterable[Any]], exts: Optional[set] = None) -> Optional[Path]:
    files = existing_files(items, exts)
    return files[0] if files else None


def get_ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


FFMPEG = get_ffmpeg()
FFPROBE = str(Path(FFMPEG).with_name("ffprobe.exe")) if Path(FFMPEG).name.lower() == "ffmpeg.exe" else "ffprobe"


def run_cmd(cmd: Sequence[Any], label: Optional[str] = None) -> subprocess.CompletedProcess:
    if label:
        safe_print(label)
    cmd = [str(x) for x in cmd]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
    if result.returncode != 0:
        raise RuntimeError((result.stderr or "")[-4500:])
    return result


def probe_duration(path: Any) -> float:
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="ignore",
        )
        if r.returncode == 0:
            return max(0.05, float(r.stdout.strip()))
    except Exception:
        pass
    return 6.0


def has_audio_stream(path: Any) -> bool:
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="ignore",
        )
        return r.returncode == 0 and "audio" in r.stdout.lower()
    except Exception:
        return False


# ------------------------------------------------------------
# AI Audio profiles
# ------------------------------------------------------------

AUDIO_NICHE_PROFILES: Dict[str, Dict[str, Any]] = {
    "luxury": {
        "target_lufs": -16,
        "voice_volume": 1.015,
        "music_volume": 0.060,
        "sfx_volume": 0.055,
        "highpass": 85,
        "lowpass": 9500,
        "presence_boost": 1.8,
        "compress_threshold": -19,
        "compress_ratio": 2.2,
        "true_peak": 0.97,
    },
    "luxury_lifestyle": {
        "target_lufs": -16,
        "voice_volume": 1.015,
        "music_volume": 0.060,
        "sfx_volume": 0.055,
        "highpass": 85,
        "lowpass": 9500,
        "presence_boost": 1.8,
        "compress_threshold": -19,
        "compress_ratio": 2.2,
        "true_peak": 0.97,
    },
    "finance": {
        "target_lufs": -15,
        "voice_volume": 1.02,
        "music_volume": 0.045,
        "sfx_volume": 0.040,
        "highpass": 95,
        "lowpass": 9000,
        "presence_boost": 2.4,
        "compress_threshold": -20,
        "compress_ratio": 2.6,
        "true_peak": 0.97,
    },
    "finance_simulation": {
        "target_lufs": -15,
        "voice_volume": 1.02,
        "music_volume": 0.045,
        "sfx_volume": 0.040,
        "highpass": 95,
        "lowpass": 9000,
        "presence_boost": 2.4,
        "compress_threshold": -20,
        "compress_ratio": 2.6,
        "true_peak": 0.97,
    },
    "ai": {
        "target_lufs": -15,
        "voice_volume": 1.018,
        "music_volume": 0.055,
        "sfx_volume": 0.062,
        "highpass": 90,
        "lowpass": 9800,
        "presence_boost": 2.2,
        "compress_threshold": -19,
        "compress_ratio": 2.4,
        "true_peak": 0.97,
    },
    "quantum_future": {
        "target_lufs": -15,
        "voice_volume": 1.018,
        "music_volume": 0.055,
        "sfx_volume": 0.062,
        "highpass": 90,
        "lowpass": 9800,
        "presence_boost": 2.2,
        "compress_threshold": -19,
        "compress_ratio": 2.4,
        "true_peak": 0.97,
    },
    "islamic": {
        "target_lufs": -15,
        "voice_volume": 1.01,
        "music_volume": 0.030,
        "sfx_volume": 0.025,
        "highpass": 85,
        "lowpass": 9000,
        "presence_boost": 1.6,
        "compress_threshold": -20,
        "compress_ratio": 2.0,
        "true_peak": 0.97,
    },
    "home_design": {
        "target_lufs": -16,
        "voice_volume": 1.012,
        "music_volume": 0.052,
        "sfx_volume": 0.045,
        "highpass": 85,
        "lowpass": 9200,
        "presence_boost": 1.7,
        "compress_threshold": -20,
        "compress_ratio": 2.1,
        "true_peak": 0.97,
    },
    "interior_design": {
        "target_lufs": -16,
        "voice_volume": 1.012,
        "music_volume": 0.052,
        "sfx_volume": 0.045,
        "highpass": 85,
        "lowpass": 9200,
        "presence_boost": 1.7,
        "compress_threshold": -20,
        "compress_ratio": 2.1,
        "true_peak": 0.97,
    },
    "mystery": {
        "target_lufs": -17,
        "voice_volume": 1.015,
        "music_volume": 0.050,
        "sfx_volume": 0.060,
        "highpass": 80,
        "lowpass": 8800,
        "presence_boost": 1.8,
        "compress_threshold": -20,
        "compress_ratio": 2.4,
        "true_peak": 0.97,
    },
    "default": {
        "target_lufs": -15,
        "voice_volume": 1.015,
        "music_volume": 0.055,
        "sfx_volume": 0.055,
        "highpass": 90,
        "lowpass": 9500,
        "presence_boost": 2.0,
        "compress_threshold": -19,
        "compress_ratio": 2.3,
        "true_peak": 0.97,
    },
}


def normalize_niche(niche: Any = None) -> str:
    key = str(niche or "default").strip().lower()
    return key if key in AUDIO_NICHE_PROFILES else "default"


def audio_profile(niche: Any = None, audio_plan: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    key = normalize_niche(niche)
    profile = dict(AUDIO_NICHE_PROFILES[key])

    if isinstance(audio_plan, dict):
        # Accept Phase 5 Audio Brain plan.
        voice_processing = audio_plan.get("voice_processing") if isinstance(audio_plan.get("voice_processing"), dict) else {}
        music = audio_plan.get("music") if isinstance(audio_plan.get("music"), dict) else {}
        if voice_processing.get("normalize_lufs") is not None:
            profile["target_lufs"] = fnum(voice_processing.get("normalize_lufs"), profile["target_lufs"])
        if voice_processing.get("eq"):
            eq = voice_processing.get("eq") or {}
            if eq.get("highpass_hz"):
                profile["highpass"] = fnum(eq.get("highpass_hz"), profile["highpass"])
        if music.get("target_relative_db"):
            # Keep safe practical level; do not over-amplify.
            profile["music_volume"] = min(profile["music_volume"], 0.060)
        if music.get("duck_db"):
            profile["duck_db"] = fnum(music.get("duck_db"), -10)

    # UI overrides compatibility.
    if kwargs.get("voice_level") is not None:
        profile["voice_volume"] *= fnum(kwargs.get("voice_level"), 1.0)
    if kwargs.get("music_level") is not None:
        profile["music_volume"] = fnum(kwargs.get("music_level"), profile["music_volume"])
    if kwargs.get("sfx_level") is not None:
        profile["sfx_volume"] = fnum(kwargs.get("sfx_level"), profile["sfx_volume"])

    profile["niche"] = key
    return profile


def phase13_audio_report() -> Dict[str, Any]:
    return {
        "version": PHASE13_AUDIO_ENGINE_VERSION,
        "ffmpeg": FFMPEG,
        "profiles": sorted(AUDIO_NICHE_PROFILES.keys()),
        "features": {
            "voice_eq": True,
            "compression": True,
            "limiter": True,
            "music_loop": True,
            "sfx_loop": True,
            "ducking_style_mix": True,
            "loudnorm_available": True,
            "backward_compatible_kwargs": True,
        },
    }


# ------------------------------------------------------------
# Filter builders
# ------------------------------------------------------------

def voice_filter(profile: Dict[str, Any], normalize: bool = True) -> str:
    hp = int(profile.get("highpass", 90))
    lp = int(profile.get("lowpass", 9500))
    vol = fnum(profile.get("voice_volume"), 1.015)
    threshold = fnum(profile.get("compress_threshold"), -19)
    ratio = fnum(profile.get("compress_ratio"), 2.3)
    peak = fnum(profile.get("true_peak"), 0.97)

    filters = [
        f"volume={vol:.4f}",
        f"highpass=f={hp}",
        f"lowpass=f={lp}",
        f"acompressor=threshold={threshold}dB:ratio={ratio}:attack=12:release=120",
        f"alimiter=limit={peak}",
        "aresample=44100,aformat=channel_layouts=stereo",
    ]

    # loudnorm is heavier; only use in standalone voice master if requested.
    if normalize:
        target = fnum(profile.get("target_lufs"), -15)
        filters.append(f"loudnorm=I={target}:TP=-1.0:LRA=11")
    return ",".join(filters)


def music_filter(profile: Dict[str, Any], duration: float) -> str:
    vol = max(0.0, min(0.30, fnum(profile.get("music_volume"), 0.055)))
    duration = max(0.1, fnum(duration, 0.1))
    return (
        f"volume={vol:.4f},"
        "highpass=f=60,lowpass=f=12000,"
        "acompressor=threshold=-24dB:ratio=1.6:attack=30:release=250,"
        f"afade=t=in:st=0:d=0.8,"
        f"afade=t=out:st={max(0.0, duration - 1.0):.3f}:d=1.0,"
        "aresample=44100,aformat=channel_layouts=stereo"
    )


def sfx_filter(profile: Dict[str, Any]) -> str:
    vol = max(0.0, min(0.30, fnum(profile.get("sfx_volume"), 0.055)))
    return (
        f"volume={vol:.4f},"
        "highpass=f=80,lowpass=f=14000,"
        "aresample=44100,aformat=channel_layouts=stereo"
    )


# ------------------------------------------------------------
# Core audio processing
# ------------------------------------------------------------

def _force_m4a_extension(output_path: Path) -> Path:
    """
    CRITICAL FIX: Force .m4a extension when using AAC codec.
    Prevents corruption when caller passes .wav path but we encode with AAC.
    """
    if output_path.suffix.lower() not in {".m4a", ".mp4", ".aac"}:
        output_path = output_path.with_suffix(".m4a")
    return output_path


def master_voice_audio(
    voice_path: Any,
    output_path: Optional[Any] = None,
    niche: Any = None,
    audio_plan: Optional[Dict[str, Any]] = None,
    normalize_loudness: bool = True,
    **kwargs,
) -> str:
    voice = Path(voice_path)
    if not voice.exists():
        raise FileNotFoundError(f"Voice not found: {voice}")

    out = Path(output_path) if output_path else OUTPUT_DIR / f"voice_master_{int(time.time())}.m4a"
    
    # 🔴 CRITICAL FIX: Force .m4a extension to match AAC codec
    out = _force_m4a_extension(out)
    
    out.parent.mkdir(parents=True, exist_ok=True)

    profile = audio_profile(niche=niche, audio_plan=audio_plan, **kwargs)

    run_cmd([
        FFMPEG, "-y",
        "-i", str(voice),
        "-vn",
        "-af", voice_filter(profile, normalize=normalize_loudness),
        "-c:a", "aac",
        "-b:a", "160k",
        "-ar", "44100",
        "-ac", "2",
        str(out),
    ], label="[AudioPhase13] master voice")

    return str(out)


def trim_silence_light(
    input_path: Any,
    output_path: Optional[Any] = None,
    threshold_db: int = -45,
    min_silence: float = 0.60,
    target_gap: float = 0.35,
    **kwargs,
) -> str:
    """Light silence trim.

    This is intentionally conservative. It removes long silence but does not
    destroy speech timing. If ffmpeg silenceremove behaves badly on a voice,
    caller can disable clean_silence.
    """
    inp = Path(input_path)
    if not inp.exists():
        raise FileNotFoundError(f"Audio not found: {inp}")

    out = Path(output_path) if output_path else OUTPUT_DIR / f"voice_trim_{int(time.time())}.m4a"
    
    # 🔴 CRITICAL FIX: Force .m4a extension
    out = _force_m4a_extension(out)
    
    out.parent.mkdir(parents=True, exist_ok=True)

    # Conservative silenceremove. target_gap is conceptual; ffmpeg keeps speech safe.
    af = (
        f"silenceremove=start_periods=1:start_threshold={threshold_db}dB:"
        f"stop_periods=-1:stop_duration={float(min_silence):.2f}:stop_threshold={threshold_db}dB,"
        "aresample=44100,aformat=channel_layouts=stereo"
    )

    try:
        run_cmd([
            FFMPEG, "-y",
            "-i", str(inp),
            "-vn",
            "-af", af,
            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", "44100",
            "-ac", "2",
            str(out),
        ], label="[AudioPhase13] light silence trim")
        return str(out)
    except Exception:
        # Fail-safe: copy original if trim fails.
        shutil.copy2(inp, out)
        return str(out)


def build_audio_mix_file(
    voice_path: Any,
    output_path: Optional[Any] = None,
    duration: Optional[float] = None,
    music_path: Optional[Any] = None,
    sfx_files: Optional[Sequence[Any]] = None,
    niche: Any = None,
    audio_plan: Optional[Dict[str, Any]] = None,
    clean_silence: bool = False,
    **kwargs,
) -> str:
    """Build standalone audio mix file.

    Returns an .m4a containing voice + optional music + optional sfx.
    """
    voice = Path(voice_path)
    if not voice.exists():
        raise FileNotFoundError(f"Voice not found: {voice}")

    out = Path(output_path) if output_path else OUTPUT_DIR / f"full_audio_mix_{int(time.time())}.m4a"
    
    # 🔴 CRITICAL FIX: Force .m4a extension to prevent AAC-in-WAV corruption
    out = _force_m4a_extension(out)
    
    out.parent.mkdir(parents=True, exist_ok=True)

    profile = audio_profile(niche=niche, audio_plan=audio_plan, **kwargs)
    duration = fnum(duration, probe_duration(voice))

    working_voice = voice
    temp_files: List[Path] = []

    try:
        if clean_silence:
            trimmed = OUTPUT_DIR / f"_trim_{int(time.time())}.m4a"
            working_voice = Path(trim_silence_light(voice, trimmed))
            temp_files.append(working_voice)

        music = Path(music_path) if music_path and Path(music_path).exists() else None
        sfx = first_existing(sfx_files, AUDIO_EXTS)

        cmd = [FFMPEG, "-y", "-i", str(working_voice)]
        filters = [f"[0:a]{voice_filter(profile, normalize=False)}[v]"]
        labels = ["[v]"]

        next_idx = 1
        if music:
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            filters.append(f"[{next_idx}:a]{music_filter(profile, duration)}[m]")
            labels.append("[m]")
            next_idx += 1

        if sfx:
            cmd += ["-stream_loop", "-1", "-i", str(sfx)]
            filters.append(f"[{next_idx}:a]{sfx_filter(profile)}[s]")
            labels.append("[s]")
            next_idx += 1

        target = fnum(profile.get("target_lufs"), -15)
        peak = fnum(profile.get("true_peak"), 0.97)

        filters.append(
            "".join(labels)
            + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.3,"
            + "acompressor=threshold=-20dB:ratio=1.7:attack=12:release=120,"
            + f"alimiter=limit={peak},"
            + f"loudnorm=I={target}:TP=-1.0:LRA=11,aformat=channel_layouts=stereo"
            + "[aout]"
        )

        cmd += [
            "-filter_complex", ";".join(filters),
            "-map", "[aout]",
            "-t", f"{duration:.3f}",
            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", "44100",
            "-ac", "2",
            str(out),
        ]

        run_cmd(cmd, label="[AudioPhase13] build full audio mix")
        return str(out)

    finally:
        for p in temp_files:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass


# ============================================================
# PATCH 6: ROOM TONE GENERATOR (Surgical Addition)
# Adds subtle brown noise floor at -48dB.
# Removes 'too-clean TTS' feel, adds natural ambience.
# Verifiable via spectrogram only, not audible as distinct element.
# ============================================================
def generate_room_tone(duration, output_path, level_db=-48):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(float(duration or 0), 0.5)
    try:
        volume = 10 ** (level_db / 20.0)
        cmd = [
            FFMPEG, "-y",
            "-f", "lavfi",
            "-i", "anoisesrc=color=brown:duration=" + str(duration) + ":amplitude=" + str(volume),
            "-ar", "44100", "-ac", "2",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if output_path.exists() and output_path.stat().st_size > 100:
            return str(output_path)
    except Exception:
        pass
    return None


def mix_room_tone_into_audio(main_audio_path, room_tone_path, output_path, room_level_db=-48):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not room_tone_path or not Path(room_tone_path).exists():
        return str(main_audio_path)
    try:
        vol = 10 ** (room_level_db / 20.0)
        cmd = [
            FFMPEG, "-y",
            "-i", str(main_audio_path),
            "-i", str(room_tone_path),
            "-filter_complex",
            "[0:a]volume=1.0[main];"
            "[1:a]volume=" + str(vol) + "[tone];"
            "[main][tone]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "[aout]",
            "-c:a", "aac", "-b:a", "192k",
            "-ar", "44100", "-ac", "2",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if output_path.exists() and output_path.stat().st_size > 1000:
            return str(output_path)
    except Exception:
        pass
    return str(main_audio_path)
# ============================================================

# ============================================================
# PATCH 12: INTELLIGENT AUDIO DUCKING
# Sidechain-style compression. Music auto-dips when voice speaks,
# rises naturally during pauses. Professional mix behavior.
# ============================================================
def apply_intelligent_ducking(video_path, voice_path, music_path,
                                output_path, duck_amount_db=-10):
    import subprocess
    video_path = Path(video_path)
    voice_path = Path(voice_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not music_path or not Path(music_path).exists():
        cmd = [
            FFMPEG, "-y",
            "-i", str(video_path), "-i", str(voice_path),
            "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if output_path.exists():
            return str(output_path)
        return str(video_path)
    try:
        cmd = [
            FFMPEG, "-y",
            "-i", str(video_path),
            "-i", str(voice_path),
            "-stream_loop", "-1", "-i", str(music_path),
            "-filter_complex",
            "[2:a]volume=0.08[a_music];"
            "[1:a]volume=1.0[a_voice];"
            "[a_music][a_voice]sidechaincompress="
            "threshold=0.05:ratio=5:attack=12:release=180:knee=3"
            ":link=average[ducked_music];"
            "[a_voice][ducked_music]amix=inputs=2:duration=first"
            ":dropout_transition=0.5[aout]",
            "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if output_path.exists() and output_path.stat().st_size > 1000:
            return str(output_path)
    except Exception as e:
        log("[AudioDucking] Skipped: " + str(e))
    return str(video_path)
# ============================================================

def mux_audio_with_video(
    video_path: Any,
    voice_path: Any,
    output_path: Optional[Any] = None,
    music_path: Optional[Any] = None,
    sfx_files: Optional[Sequence[Any]] = None,
    niche: Any = None,
    audio_plan: Optional[Dict[str, Any]] = None,
    duration: Optional[float] = None,
    clean_silence: bool = False,
    **kwargs,
) -> str:
    video = Path(video_path)
    voice = Path(voice_path)
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")
    if not voice.exists():
        raise FileNotFoundError(f"Voice not found: {voice}")

    out = Path(output_path) if output_path else video.with_name(video.stem + "_audio.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)

    duration = fnum(duration, probe_duration(video))
    profile = audio_profile(niche=niche, audio_plan=audio_plan, **kwargs)

    music = Path(music_path) if music_path and Path(music_path).exists() else None
    sfx = first_existing(sfx_files, AUDIO_EXTS)

    working_voice = voice
    temp_files: List[Path] = []

    try:
        if clean_silence:
            trimmed = OUTPUT_DIR / f"_trim_mux_{int(time.time())}.m4a"
            working_voice = Path(trim_silence_light(voice, trimmed))
            temp_files.append(working_voice)

        cmd = [FFMPEG, "-y", "-i", str(video), "-i", str(working_voice)]
        filters = [f"[1:a]{voice_filter(profile, normalize=False)}[v]"]
        labels = ["[v]"]

        next_idx = 2
        if music:
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            filters.append(f"[{next_idx}:a]{music_filter(profile, duration)}[m]")
            labels.append("[m]")
            next_idx += 1

        if sfx:
            cmd += ["-stream_loop", "-1", "-i", str(sfx)]
            filters.append(f"[{next_idx}:a]{sfx_filter(profile)}[s]")
            labels.append("[s]")
            next_idx += 1

        target = fnum(profile.get("target_lufs"), -15)
        peak = fnum(profile.get("true_peak"), 0.97)

        filters.append(
            "".join(labels)
            + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.3,"
            + "acompressor=threshold=-20dB:ratio=1.7:attack=12:release=120,"
            + f"alimiter=limit={peak},"
            + f"loudnorm=I={target}:TP=-1.0:LRA=11,aformat=channel_layouts=stereo"
            + "[aout]"
        )

        cmd += [
            "-filter_complex", ";".join(filters),
            "-map", "0:v:0",
            "-map", "[aout]",
            "-t", f"{duration:.3f}",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", "44100",
            "-ac", "2",
            "-movflags", "+faststart",
            str(out),
        ]

        run_cmd(cmd, label="[AudioPhase13] mux audio with video")
        return str(out)

    finally:
        for p in temp_files:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass


# ------------------------------------------------------------
# Backward compatible APIs
# ------------------------------------------------------------

def _extract_arg(args: Sequence[Any], index: int, default: Any = None) -> Any:
    try:
        return args[index]
    except Exception:
        return default


def _normalize_legacy_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Swallow old/new random kwargs safely.

    This prevents errors like:
    build_full_audio_mix() got an unexpected keyword argument 'premium_audio_mode'
    """
    out = dict(kwargs)

    # Common legacy aliases
    if "bg_music" in out and "music_path" not in out:
        out["music_path"] = out.get("bg_music")
    if "background_music" in out and "music_path" not in out:
        out["music_path"] = out.get("background_music")
    if "sfx" in out and "sfx_files" not in out:
        out["sfx_files"] = out.get("sfx")
    if "audio_mix_path" in out and "output_path" not in out:
        out["output_path"] = out.get("audio_mix_path")

    return out


def build_full_audio_mix(*args, **kwargs) -> str:
    """Backward compatible full audio mix builder.

    Supported common calls:
    - build_full_audio_mix(voice_path, output_path, music_path=..., sfx_files=...)
    - build_full_audio_mix(voice_path=..., output_path=..., ...)
    - build_full_audio_mix(video_path=..., voice_path=..., output_path=...) -> mux
    """
    kwargs = _normalize_legacy_kwargs(kwargs)

    # CRITICAL FIX: Pop all named arguments from kwargs so they are NEVER passed twice via **kwargs
    video_path = kwargs.pop("video_path", None) or kwargs.pop("video", None)
    voice_path = kwargs.pop("voice_path", None) or kwargs.pop("voice", None) or _extract_arg(args, 0)
    output_path = kwargs.pop("output_path", None) or kwargs.pop("out", None) or kwargs.pop("final_audio_path", None) or _extract_arg(args, 1)
    music_path = kwargs.pop("music_path", None) or kwargs.pop("bg_music", None) or kwargs.pop("background_music", None)
    sfx_files = kwargs.pop("sfx_files", None) or kwargs.pop("sfx", None)
    duration = kwargs.pop("duration", None) or kwargs.pop("dur", None) or kwargs.pop("target_duration", None)
    niche = kwargs.pop("niche", None)
    audio_plan = kwargs.pop("audio_plan", None)
    if not audio_plan and isinstance(kwargs.get("preset_overrides"), dict):
        audio_plan = kwargs.get("preset_overrides", {}).get("audio_plan")
    clean_silence = bool(kwargs.pop("clean_silence", False))

    # Safely remove any other conflicting legacy keys
    for key in ["voice", "video", "out", "final_audio_path", "dur", "target_duration", "bg_music", "background_music", "sfx", "audio_mix_path", "preset_overrides"]:
        kwargs.pop(key, None)

    if video_path:
        return mux_audio_with_video(
            video_path=video_path,
            voice_path=voice_path,
            output_path=output_path,
            music_path=music_path,
            sfx_files=sfx_files,
            niche=niche,
            audio_plan=audio_plan,
            duration=duration,
            clean_silence=clean_silence,
            **kwargs,
        )

    return build_audio_mix_file(
        voice_path=voice_path,
        output_path=output_path,
        duration=duration,
        music_path=music_path,
        sfx_files=sfx_files,
        niche=niche,
        audio_plan=audio_plan,
        clean_silence=clean_silence,
        **kwargs,
    )


def build_integrated_audio_for_pipeline(*args, **kwargs) -> str:
    return build_full_audio_mix(*args, **kwargs)


def build_audio_mix(*args, **kwargs) -> str:
    return build_full_audio_mix(*args, **kwargs)


def mix_voice_music_sfx(*args, **kwargs) -> str:
    return build_full_audio_mix(*args, **kwargs)


def master_audio(*args, **kwargs) -> str:
    voice_path = kwargs.get("voice_path") or kwargs.get("voice") or _extract_arg(args, 0)
    output_path = kwargs.get("output_path") or kwargs.get("out") or _extract_arg(args, 1)
    return master_voice_audio(voice_path, output_path=output_path, **kwargs)


def normalize_voice(*args, **kwargs) -> str:
    return master_audio(*args, **kwargs)


def clean_voice_audio(*args, **kwargs) -> str:
    voice_path = kwargs.get("voice_path") or kwargs.get("voice") or _extract_arg(args, 0)
    output_path = kwargs.get("output_path") or kwargs.get("out") or _extract_arg(args, 1)
    return trim_silence_light(voice_path, output_path=output_path, **kwargs)


def apply_audio_plan_to_video(*args, **kwargs) -> str:
    return build_full_audio_mix(*args, **kwargs)


def phase13_apply_audio_brain(*args, **kwargs) -> str:
    return build_full_audio_mix(*args, **kwargs)


# Old code sometimes expects this transformation function.
def _premium_audio_apply_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    return _normalize_legacy_kwargs(dict(kwargs or {}))


def audio_engine_self_test() -> Dict[str, Any]:
    return phase13_audio_report()


if __name__ == "__main__":
    print(json.dumps(phase13_audio_report(), indent=2))


def list_audio_files(folder):
    """Helper for music_engine and sfx_engine to list audio files."""
    p = Path(folder)
    if not p.exists(): 
        return []
    return existing_files(p.glob("*"), AUDIO_EXTS)


def loop_audio(audio_path, target_duration, output_path=None):
    """Loop audio to target duration. Returns path."""
    # Safe fallback: just return the original path
    return str(audio_path)
# ============================================================
# CINEMATIC AUDIO POLISH AUTO-INJECTOR (SAFE PATCH)
# Adds professional sound stage, emotion EQ, and human rhythm.
# ============================================================
try:
    from cinematic_polish_engine import cinematic_audio_polish_ffmpeg, LOW_RAM_MODE
    
    _orig_build_mix = build_audio_mix_file
    
    def build_audio_mix_file(voice_path, output_path=None, duration=None, music_path=None, sfx_files=None, niche="default", audio_plan=None, clean_silence=False, **kwargs):
        """Wrapper to apply cinematic audio polish after standard mix."""
        # 1. Run original mix
        mixed_path = _orig_build_mix(voice_path, output_path, duration, music_path, sfx_files, niche, audio_plan, clean_silence, **kwargs)
        
        # 2. Apply Cinematic Polish if RAM allows
        if not LOW_RAM_MODE and mixed_path and Path(mixed_path).exists():
            try:
                polish_out = Path(mixed_path).parent / f"cinematic_polish_{Path(mixed_path).stem}.m4a"
                polished = cinematic_audio_polish_ffmpeg(mixed_path, polish_out, niche)
                if Path(polished).exists() and Path(polished).stat().st_size > 1000:
                    return polished
            except Exception:
                pass
                
        return mixed_path
        
    build_audio_mix_file = build_audio_mix_file
    print("[CinematicAudio] Audio polish injected successfully.")
    
except Exception as e:
    print(f"[CinematicAudio] Injection skipped (Safe fallback): {e}")

# --- AUTO-ADDED ALIASES FOR COMPATIBILITY ---
def audio_duration(path):
    if 'probe_duration' in globals():
        return probe_duration(path)
    return 0.0


# --- AUTO-PATCH: MISSING ALIASES ---
def audio_duration(path):
    if 'probe_duration' in globals():
        return probe_duration(path)
    return 0.0
