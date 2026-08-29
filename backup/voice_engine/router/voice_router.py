"""
VOICE ROUTER
============

Loads niche profile
Applies variation
Returns final profile
"""

from voice_engine.profiles.niche_profiles import VOICE_PROFILES
from voice_engine.humanizer.variation_engine import generate_humanized_profile


DEFAULT_PROFILE = "auto"


AUTO_PROFILE_MAP = {
    "finance": "finance_simulation",
    "money": "finance_simulation",
    "economy": "finance_simulation",

    "luxury": "luxury_lifestyle",
    "wealth": "luxury_lifestyle",

    "mystery": "mystery",
    "crime": "mystery",

    "design": "interior_design",
    "home": "interior_design",

    "stoic": "stoic_wisdom",
    "wisdom": "stoic_wisdom",

    "future": "quantum_future",
    "ai": "quantum_future",
    "technology": "quantum_future",
}


def get_profile(profile_id):

    if profile_id in VOICE_PROFILES:
        return VOICE_PROFILES[profile_id]

    return VOICE_PROFILES["quantum_future"]


def auto_detect_profile(text):

    text = str(text).lower()

    for keyword, profile in AUTO_PROFILE_MAP.items():

        if keyword in text:
            return profile

    return "quantum_future"


def get_final_voice_profile(
    selected_profile,
    content_hint="",
    seed=None
):

    if selected_profile == "auto":

        selected_profile = auto_detect_profile(
            content_hint
        )

    base_profile = get_profile(
        selected_profile
    )

    final_profile = generate_humanized_profile(
        base_profile,
        seed=seed
    )

    final_profile["profile_id"] = selected_profile

    return final_profile