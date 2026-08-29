"""
HUMAN VARIATION ENGINE
======================

Purpose:
Same niche ki har video me exact same voice settings na lagen.

Example:
Quantum Future video #1:
    speed 0.920
    stability 28

Quantum Future video #2:
    speed 0.914
    stability 30

Quantum Future video #3:
    speed 0.927
    stability 27

Base personality same rahegi.
Lekin micro variation voice ko human banayegi.
"""

import copy
import random


VARIATION_RULES = {
    "voice": {
        "stability": (-3, 3),
        "similarity": (-2, 2),
        "style": (-3, 3),
        "speed": (-0.012, 0.012),
        "pitch": (-0.03, 0.03),
        "energy": (-0.04, 0.04),
    },

    "pauses": {
        "comma": (-0.03, 0.04),
        "thinking": (-0.08, 0.10),
        "dramatic": (-0.10, 0.12),
        "reveal": (-0.15, 0.18),
    },

    "breathing": {
        "volume_db": (-2, 2),
    },

    "eq": {
        "warmth_db": (-0.3, 0.3),
        "mud_cut_db": (-0.3, 0.3),
        "presence_db": (-0.3, 0.3),
        "air_db": (-0.2, 0.2),
    },

    "compression": {
        "threshold": (-1.5, 1.5),
        "attack": (-3, 3),
        "release": (-10, 10),
    },

    "deesser": {
        "reduction": (-0.5, 0.5),
    },

    "single_values": {
        "saturation": (-1, 1),
        "reverb": (-0.8, 0.8),
        "music_db": (-2, 2),
    }
}


SAFE_LIMITS = {
    "voice": {
        "stability": (20, 60),
        "similarity": (75, 95),
        "style": (10, 45),
        "speed": (0.86, 0.98),
        "pitch": (-0.15, 0.15),
        "energy": (0.25, 0.65),
    },

    "pauses": {
        "comma": (0.12, 0.30),
        "thinking": (0.45, 1.10),
        "dramatic": (0.70, 1.50),
        "reveal": (1.00, 1.90),
    },

    "breathing": {
        "volume_db": (-42, -30),
    },

    "eq": {
        "warmth_db": (1.0, 2.5),
        "mud_cut_db": (-2.8, -1.0),
        "presence_db": (1.0, 2.8),
        "air_db": (0.5, 2.3),
    },

    "compression": {
        "threshold": (-24, -18),
        "attack": (15, 30),
        "release": (80, 140),
    },

    "deesser": {
        "reduction": (1.5, 4.5),
    },

    "single_values": {
        "saturation": (4, 10),
        "reverb": (2, 7),
        "music_db": (-34, -24),
    }
}


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def random_variation(amount_range):
    low, high = amount_range
    return random.uniform(low, high)


def vary_number(value, amount_range, safe_range=None):
    new_value = value + random_variation(amount_range)

    if safe_range:
        new_value = clamp(new_value, safe_range[0], safe_range[1])

    if isinstance(value, int):
        return int(round(new_value))

    return round(new_value, 3)


def apply_nested_variation(profile, section_name):
    if section_name not in profile:
        return

    if section_name not in VARIATION_RULES:
        return

    section = profile[section_name]
    rules = VARIATION_RULES[section_name]
    limits = SAFE_LIMITS.get(section_name, {})

    for key, amount_range in rules.items():
        if key not in section:
            continue

        safe_range = limits.get(key)
        section[key] = vary_number(
            section[key],
            amount_range,
            safe_range
        )


def apply_single_value_variation(profile):
    rules = VARIATION_RULES["single_values"]
    limits = SAFE_LIMITS["single_values"]

    for key, amount_range in rules.items():
        if key not in profile:
            continue

        profile[key] = vary_number(
            profile[key],
            amount_range,
            limits.get(key)
        )


def generate_humanized_profile(base_profile, seed=None):
    """
    Main function.

    Input:
        base_profile from niche_profiles.py

    Output:
        new profile with micro human variation
    """

    if seed is not None:
        random.seed(seed)

    profile = copy.deepcopy(base_profile)

    apply_nested_variation(profile, "voice")
    apply_nested_variation(profile, "pauses")
    apply_nested_variation(profile, "breathing")
    apply_nested_variation(profile, "eq")
    apply_nested_variation(profile, "compression")
    apply_nested_variation(profile, "deesser")
    apply_single_value_variation(profile)

    profile["variation_applied"] = True
    profile["variation_note"] = "Controlled micro variation applied for human realism."

    return profile


def preview_variations(base_profile, count=3):
    previews = []

    for i in range(count):
        previews.append(
            generate_humanized_profile(
                base_profile,
                seed=random.randint(1000, 999999)
            )
        )

    return previews