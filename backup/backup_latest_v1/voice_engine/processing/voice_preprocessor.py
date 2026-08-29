"""
VOICE PREPROCESSOR
==================

Purpose:
Raw / robotic AI voice ko humanized voice me convert karna.

This file:
- voice folder me best voice file automatically pick karta hai
- priority:
    1) .wav
    2) .mp3
    3) .m4a
    4) .aac
- selected niche profile load karta hai
- human variation apply karta hai
- ffmpeg audio filters apply karta hai
- humanized voice output save karta hai

Important:
Ye actual audio-processing layer hai.
"""

import os
import subprocess
from datetime import datetime


BASE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

SHORT_VOICE_DIR = os.path.join(
    BASE,
    "inputs",
    "shorts",
    "voices"
)

LONG_VOICE_DIR = os.path.join(
    BASE,
    "inputs",
    "long",
    "voices"
)

OUTPUT_DIR = os.path.join(
    BASE,
    "voice_engine",
    "outputs"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FILE HELPERS
# ============================================================
def safe_path(path):
    return os.path.abspath(path)


def find_best_voice_file(voice_folder):
    """
    Voice folder se best available voice file pick karta hai.

    Priority:
        1) WAV
        2) MP3
        3) M4A
        4) AAC

    Reason:
        WAV usually highest quality hoti hai.
        Agar WAV available hai to usko prefer karna chahiye.
        Agar WAV nahi hai to MP3 use hogi.
    """

    voice_folder = safe_path(voice_folder)

    if not os.path.exists(voice_folder):
        raise RuntimeError(
            f"Voice folder not found: {voice_folder}"
        )

    files = os.listdir(voice_folder)

    wav_files = sorted([
        f for f in files
        if f.lower().endswith(".wav")
    ])

    if wav_files:
        return os.path.join(
            voice_folder,
            wav_files[0]
        )

    mp3_files = sorted([
        f for f in files
        if f.lower().endswith(".mp3")
    ])

    if mp3_files:
        return os.path.join(
            voice_folder,
            mp3_files[0]
        )

    m4a_files = sorted([
        f for f in files
        if f.lower().endswith(".m4a")
    ])

    if m4a_files:
        return os.path.join(
            voice_folder,
            m4a_files[0]
        )

    aac_files = sorted([
        f for f in files
        if f.lower().endswith(".aac")
    ])

    if aac_files:
        return os.path.join(
            voice_folder,
            aac_files[0]
        )

    raise RuntimeError(
        f"No supported voice file found in: {voice_folder}"
    )


# ============================================================
# AUDIO FILTER HELPERS
# ============================================================
def db_to_linear(db_value):
    """
    dB value ko linear limiter value me convert karta hai.

    Example:
        -1 dB ≈ 0.8913
    """

    try:
        return round(
            10 ** (float(db_value) / 20),
            4
        )
    except Exception:
        return 0.8913


def build_ffmpeg_audio_filter(profile):
    """
    Profile ke EQ / compression / saturation / reverb values ko
    ffmpeg audio filter chain me convert karta hai.

    Ye chain voice ko:
        - cleaner
        - warmer
        - less robotic
        - more controlled
        - more YouTube-ready
    banati hai.
    """

    eq = profile.get("eq", {})
    comp = profile.get("compression", {})
    deesser = profile.get("deesser", {})

    hpf = eq.get("hpf", 80)

    warmth_db = eq.get("warmth_db", 1.5)
    warmth_freq = eq.get("warmth_freq", 150)

    mud_cut_db = eq.get("mud_cut_db", -2)
    mud_freq = eq.get("mud_freq", 300)

    presence_db = eq.get("presence_db", 2)
    presence_freq = eq.get("presence_freq", 4000)

    air_db = eq.get("air_db", 1)
    air_freq = eq.get("air_freq", 10000)

    threshold = comp.get("threshold", -20)
    ratio = comp.get("ratio", 2.5)
    attack = comp.get("attack", 20)
    release = comp.get("release", 120)

    deess_freq = deesser.get("freq", 6500)
    deess_reduction = deesser.get("reduction", 3)

    saturation = profile.get("saturation", 6)
    reverb = profile.get("reverb", 4)
    peak_db = profile.get("peak_db", -1)

    saturation_gain = 1.0 + (
        float(saturation) / 100.0
    )

    reverb_decay = 40 + int(
        float(reverb) * 5
    )

    reverb_wet = 0.08 + (
        float(reverb) / 100.0
    )

    limiter_value = db_to_linear(
        peak_db
    )

    filters = [
        f"highpass=f={hpf}",

        f"equalizer=f={warmth_freq}:t=q:w=1.0:g={warmth_db}",
        f"equalizer=f={mud_freq}:t=q:w=1.0:g={mud_cut_db}",
        f"equalizer=f={presence_freq}:t=q:w=1.0:g={presence_db}",
        f"equalizer=f={air_freq}:t=q:w=1.0:g={air_db}",

        (
            "acompressor="
            f"threshold={threshold}dB:"
            f"ratio={ratio}:"
            f"attack={attack}:"
            f"release={release}:"
            "makeup=1"
        ),

        f"equalizer=f={deess_freq}:t=q:w=2.0:g=-{deess_reduction}",

        f"volume={saturation_gain}",

        (
            "aecho="
            "0.8:"
            f"{reverb_wet}:"
            f"{reverb_decay}:"
            "0.08"
        ),

        "loudnorm=I=-16:TP=-1.0:LRA=11",

        f"alimiter=limit={limiter_value}"
    ]

    return ",".join(filters)


# ============================================================
# MAIN HUMANIZER
# ============================================================
def humanize_voice_file(
    input_audio,
    profile,
    output_audio=None
):
    """
    Main audio processing function.

    Args:
        input_audio:
            raw voice mp3/wav/m4a/aac path

        profile:
            final profile from voice_master_engine

        output_audio:
            optional output path

    Returns:
        output_audio path
    """

    input_audio = safe_path(input_audio)

    if not os.path.exists(input_audio):
        raise FileNotFoundError(
            f"Input voice not found: {input_audio}"
        )

    profile_id = profile.get(
        "profile_id",
        "voice"
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    if output_audio is None:
        output_audio = os.path.join(
            OUTPUT_DIR,
            f"humanized_{profile_id}_{timestamp}.mp3"
        )

    output_audio = safe_path(output_audio)

    audio_filter = build_ffmpeg_audio_filter(
        profile
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_audio,
        "-af",
        audio_filter,
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "192k",
        output_audio
    ]

    print("")
    print("========================================")
    print("VOICE PREPROCESSOR")
    print("========================================")
    print("Input:", input_audio)
    print("Output:", output_audio)
    print("Profile:", profile.get("name"))
    print("Profile ID:", profile_id)
    print("Filter:", audio_filter)
    print("========================================")
    print("")

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(
            "FFmpeg voice preprocessing failed"
        )

    print("✅ Humanized voice saved:", output_audio)

    return output_audio


def humanize_best_short_voice(
    selected_profile="auto",
    content_hint="",
    seed=None
):
    """
    Shorts voice folder se best voice file pick karta hai
    aur usko humanize karta hai.
    """

    from voice_engine.voice_master_engine import (
        build_voice_humanization_profile
    )

    input_audio = find_best_voice_file(
        SHORT_VOICE_DIR
    )

    print("🎙 Selected Short Voice:", input_audio)

    profile = build_voice_humanization_profile(
        selected_profile=selected_profile,
        content_hint=content_hint,
        seed=seed,
        save_report=True
    )

    return humanize_voice_file(
        input_audio=input_audio,
        profile=profile
    )


def humanize_best_long_voice(
    selected_profile="auto",
    content_hint="",
    seed=None
):
    """
    Long voice folder se best voice file pick karta hai
    aur usko humanize karta hai.
    """

    from voice_engine.voice_master_engine import (
        build_voice_humanization_profile
    )

    input_audio = find_best_voice_file(
        LONG_VOICE_DIR
    )

    print("🎙 Selected Long Voice:", input_audio)

    profile = build_voice_humanization_profile(
        selected_profile=selected_profile,
        content_hint=content_hint,
        seed=seed,
        save_report=True
    )

    return humanize_voice_file(
        input_audio=input_audio,
        profile=profile
    )


# ============================================================
# SCRIPT TEST
# ============================================================
if __name__ == "__main__":
    print("")
    print("========================================")
    print("VOICE PREPROCESSOR TEST MODE")
    print("========================================")
    print("Priority:")
    print("1) WAV")
    print("2) MP3")
    print("3) M4A")
    print("4) AAC")
    print("========================================")
    print("")

    output = humanize_best_short_voice(
        selected_profile="auto",
        content_hint="AI future documentary"
    )

    print("")
    print("✅ Test completed.")
    print("✅ Output:", output)