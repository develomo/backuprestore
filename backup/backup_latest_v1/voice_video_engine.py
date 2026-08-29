# voice_video_engine.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# VOICE VIDEO ENGINE v2.0
# ==========================================================
# Purpose:
# - Old polish_voice(input_audio, output_audio) function compatibility.
# - FFmpeg-based safe voice polishing.
# - Missing imports/crashes fix karna.
# - Voice ko clean, clear, and video-ready banana.
# - professional_voice_engine.py ke advanced system ko prefer karna.
#
# Old file issue:
# - subprocess import missing tha.
# - Function output return nahi kar raha tha.
# - Filter chain fixed thi, niche/mode aware nahi thi.
#
# New file:
# - subprocess imported.
# - safe error handling.
# - short/long mode support.
# - optional advanced engine integration.
# - FFmpeg fallback.
# ==========================================================

import subprocess
from pathlib import Path


# ==========================================================
# OPTIONAL ADVANCED ENGINE
# ==========================================================

try:
    from professional_voice_engine import humanize_voice_file
    ADVANCED_VOICE_AVAILABLE = True
except Exception as e:
    print(f"[VoiceVideoEngine] professional_voice_engine unavailable: {e}", flush=True)
    ADVANCED_VOICE_AVAILABLE = False
    humanize_voice_file = None


# ==========================================================
# HELPERS
# ==========================================================

def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-"), flush=True)
    except Exception:
        pass


def _mode_key(mode):
    mode = str(mode or "short").lower()
    if mode in ("long", "youtube_long", "horizontal"):
        return "long"
    return "short"


def _run(cmd):
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False,
    )

    if result.returncode != 0:
        safe_print(result.stderr)
        raise RuntimeError("VoiceVideoEngine FFmpeg command failed")

    return True


# ==========================================================
# FFMPEG FALLBACK
# ==========================================================

def ffmpeg_polish_voice(input_audio, output_audio, mode="short"):
    input_audio = Path(input_audio)
    output_audio = Path(output_audio)

    if not input_audio.exists():
        raise FileNotFoundError(f"Input audio not found: {input_audio}")

    output_audio.parent.mkdir(parents=True, exist_ok=True)

    mode = _mode_key(mode)

    if mode == "long":
        target_lufs = "-16"
        compressor = "acompressor=threshold=-20dB:ratio=2.0:attack=10:release=90"
    else:
        target_lufs = "-15"
        compressor = "acompressor=threshold=-19dB:ratio=2.3:attack=6:release=70"

    af = (
        "highpass=f=80,"
        "lowpass=f=12000,"
        "equalizer=f=3500:t=q:w=1.2:g=-1.0,"
        f"{compressor},"
        f"loudnorm=I={target_lufs}:TP=-1.5:LRA=10:linear=true"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_audio),
        "-af", af,
        "-ar", "44100",
        "-ac", "2",
        str(output_audio),
    ]

    safe_print(f"[VoiceVideoEngine] FFmpeg voice polish | mode={mode}")
    _run(cmd)
    return str(output_audio)


# ==========================================================
# PUBLIC API
# ==========================================================

def polish_voice(
    input_audio,
    output_audio,
    mode="short",
    content_hint=None,
    use_advanced=True,
):
    """
    Old-compatible function.

    Args:
        input_audio:
            source voice path.

        output_audio:
            output voice path.

        mode:
            short/long.

        content_hint:
            optional niche.

        use_advanced:
            if True, tries professional_voice_engine first.

    Returns:
        output path string.
    """
    input_audio = Path(input_audio)
    output_audio = Path(output_audio)

    if use_advanced and ADVANCED_VOICE_AVAILABLE and humanize_voice_file is not None:
        try:
            return humanize_voice_file(
                input_audio=str(input_audio),
                output_audio=str(output_audio),
                mode=mode,
                content_hint=content_hint,
            )
        except Exception as e:
            safe_print(f"[VoiceVideoEngine] Advanced polish failed, fallback used: {e}")

    return ffmpeg_polish_voice(
        input_audio=input_audio,
        output_audio=output_audio,
        mode=mode,
    )


def clean_voice(input_audio, output_audio, mode="short", content_hint=None):
    return polish_voice(
        input_audio=input_audio,
        output_audio=output_audio,
        mode=mode,
        content_hint=content_hint,
    )


def master_voice_for_video(input_audio, output_audio, mode="short", content_hint=None):
    return polish_voice(
        input_audio=input_audio,
        output_audio=output_audio,
        mode=mode,
        content_hint=content_hint,
    )


if __name__ == "__main__":
    print("Voice Video Engine ready.")
