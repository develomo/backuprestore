"""
VOICE SETTINGS MANAGER
======================

Purpose:
Voice Humanization settings ko ui_settings.json me save/load karna.

This connects:
    UI
    ↓
    ui_settings.json
    ↓
    voice_master_engine
    ↓
    pipeline

Important:
    Ye file audio process nahi karti.
    Ye sirf settings read/write karti hai.
"""

import json
import os
from datetime import datetime


BASE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)


DEFAULT_VOICE_SETTINGS = {
    "voice_humanization_enabled": True,
    "voice_profile": "auto",
    "voice_humanization_level": "balanced",
    "voice_content_hint": "",
    "voice_apply_to_short": True,
    "voice_apply_to_long": True,

    "voice_enable_eq": True,
    "voice_enable_compression": True,
    "voice_enable_deesser": True,
    "voice_enable_saturation": True,
    "voice_enable_reverb": True,
    "voice_enable_limiter": True,

    "voice_enable_breathing": True,
    "voice_enable_pause_engineering": True,
    "voice_enable_emphasis": True,
    "voice_enable_volume_automation": True,
    "voice_enable_speed_automation": True,

    "voice_music_matching": "auto",

    "voice_last_profile_id": "",
    "voice_last_profile_name": "",
    "voice_last_speed": 0.0,
    "voice_last_stability": 0,
    "voice_last_similarity": 0,
    "voice_last_style": 0,
    "voice_last_music_db": 0,
    "voice_last_variation_applied": False,
}


def load_ui_settings():
    if not os.path.exists(SETTINGS_PATH):
        return {}

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print("⚠ Failed to load ui_settings.json:", e)
        return {}


def save_ui_settings(settings):
    settings["last_updated"] = datetime.now().isoformat()

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

    print("✅ ui_settings.json updated:", SETTINGS_PATH)


def ensure_voice_settings():
    settings = load_ui_settings()

    changed = False

    for key, value in DEFAULT_VOICE_SETTINGS.items():
        if key not in settings:
            settings[key] = value
            changed = True

    if changed:
        save_ui_settings(settings)

    return settings


def update_voice_settings(
    voice_profile="auto",
    humanization_level="balanced",
    content_hint="",
    apply_to_short=True,
    apply_to_long=True,
    enabled=True,
    music_matching="auto"
):
    settings = ensure_voice_settings()

    settings["voice_humanization_enabled"] = bool(enabled)
    settings["voice_profile"] = voice_profile
    settings["voice_humanization_level"] = humanization_level
    settings["voice_content_hint"] = content_hint
    settings["voice_apply_to_short"] = bool(apply_to_short)
    settings["voice_apply_to_long"] = bool(apply_to_long)
    settings["voice_music_matching"] = music_matching

    save_ui_settings(settings)

    return settings


def save_last_generated_voice_profile(profile):
    """
    Voice Master Engine jab profile generate kare,
    uska short summary ui_settings.json me save kar sakta hai.
    """

    settings = ensure_voice_settings()

    voice = profile.get("voice", {})

    settings["voice_last_profile_id"] = profile.get("profile_id", "")
    settings["voice_last_profile_name"] = profile.get("name", "")
    settings["voice_last_speed"] = voice.get("speed", 0.0)
    settings["voice_last_stability"] = voice.get("stability", 0)
    settings["voice_last_similarity"] = voice.get("similarity", 0)
    settings["voice_last_style"] = voice.get("style", 0)
    settings["voice_last_music_db"] = profile.get("music_db", 0)
    settings["voice_last_variation_applied"] = bool(
        profile.get("variation_applied", False)
    )

    save_ui_settings(settings)

    return settings


if __name__ == "__main__":
    settings = ensure_voice_settings()

    print("")
    print("====================================")
    print("VOICE SETTINGS MANAGER")
    print("====================================")
    print("voice_humanization_enabled:", settings.get("voice_humanization_enabled"))
    print("voice_profile:", settings.get("voice_profile"))
    print("voice_humanization_level:", settings.get("voice_humanization_level"))
    print("voice_apply_to_short:", settings.get("voice_apply_to_short"))
    print("voice_apply_to_long:", settings.get("voice_apply_to_long"))
    print("voice_music_matching:", settings.get("voice_music_matching"))
    print("====================================")