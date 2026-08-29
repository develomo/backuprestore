"""
VOICE MASTER ENGINE
===================

This is the central public API for the Voice Humanization System.

Flow:
    UI / Pipeline
        ↓
    voice_master_engine.py
        ↓
    voice_router.py
        ↓
    niche profile
        ↓
    human variation
        ↓
    final voice settings

Important:
    This file abhi audio ko physically process nahi kar rahi.
    Ye final humanized profile generate karti hai.

Next steps me:
    - pause_engine.py
    - breathing_engine.py
    - ffmpeg_voice_processor.py
    - voice UI integration
add honge.
"""

import json
import os
from datetime import datetime

from voice_engine.router.voice_router import get_final_voice_profile


BASE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_voice_humanization_profile(
    selected_profile="auto",
    content_hint="",
    seed=None,
    save_report=True
):
    """
    Main function.

    Args:
        selected_profile:
            quantum_future
            stoic_wisdom
            luxury_lifestyle
            mystery
            interior_design
            finance_simulation
            auto

        content_hint:
            Script title, niche name, video idea, or topic.

        seed:
            Optional seed for repeatable testing.

        save_report:
            If True, saves profile JSON into outputs folder.

    Returns:
        final_profile dict
    """

    final_profile = get_final_voice_profile(
        selected_profile=selected_profile,
        content_hint=content_hint,
        seed=seed
    )

    final_profile["created_at"] = datetime.now().isoformat()
    final_profile["selected_profile_input"] = selected_profile
    final_profile["content_hint"] = content_hint

    if save_report:
        save_voice_profile_report(final_profile)

    return final_profile


def save_voice_profile_report(profile):
    profile_id = profile.get("profile_id", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = os.path.join(
        OUTPUT_DIR,
        f"voice_profile_{profile_id}_{timestamp}.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4, ensure_ascii=False)

    print("✅ Voice profile report saved:", output_path)

    return output_path


def build_profile_summary(profile):
    """
    Small readable summary for UI/logs.
    """

    voice = profile.get("voice", {})
    pauses = profile.get("pauses", {})
    breathing = profile.get("breathing", {})

    return {
        "profile_id": profile.get("profile_id"),
        "name": profile.get("name"),
        "speed": voice.get("speed"),
        "stability": voice.get("stability"),
        "similarity": voice.get("similarity"),
        "style": voice.get("style"),
        "pitch": voice.get("pitch"),
        "energy": voice.get("energy"),
        "comma_pause": pauses.get("comma"),
        "thinking_pause": pauses.get("thinking"),
        "dramatic_pause": pauses.get("dramatic"),
        "reveal_pause": pauses.get("reveal"),
        "breath_volume_db": breathing.get("volume_db"),
        "music_db": profile.get("music_db"),
        "saturation": profile.get("saturation"),
        "reverb": profile.get("reverb"),
        "variation_applied": profile.get("variation_applied"),
    }


def print_profile_summary(profile):
    summary = build_profile_summary(profile)

    print("")
    print("========================================")
    print("VOICE HUMANIZATION PROFILE SUMMARY")
    print("========================================")

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("========================================")
    print("")


if __name__ == "__main__":
    profile = build_voice_humanization_profile(
        selected_profile="auto",
        content_hint="A future AI system begins controlling human decisions",
        save_report=True
    )

    print_profile_summary(profile)