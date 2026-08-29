"""
BREATH ENGINE
=============

Purpose:
Niche-specific breathing intelligence generate karna.

Ye file abhi audio me breath insert nahi karti.
Ye breath plan banati hai jo later voice_preprocessor.py use karega.

Goal:
AI voice ko completely flat robotic delivery se nikal kar
subtle human narration feel dena.

Supported niches:
- quantum_future
- stoic_wisdom
- luxury_lifestyle
- mystery
- interior_design
- finance_simulation
"""


BREATH_RULES = {
    "quantum_future": {
        "style": "subtle_cinematic_breath",
        "placement": [
            "after_hook",
            "before_big_reveal",
            "before_emotional_question",
            "after_long_sentence"
        ],
        "base_count": 4,
        "intensity": "medium",
        "reason": "Future documentary voice needs subtle breath before tension and reveal."
    },

    "stoic_wisdom": {
        "style": "calm_reflective_breath",
        "placement": [
            "before_realization",
            "after_deep_observation",
            "before_final_lesson"
        ],
        "base_count": 3,
        "intensity": "low",
        "reason": "Stoic voice needs controlled breath to feel mature, calm and thoughtful."
    },

    "luxury_lifestyle": {
        "style": "minimal_elegant_breath",
        "placement": [
            "between_luxury_descriptions",
            "before_refined_statement",
            "before_soft_ending"
        ],
        "base_count": 2,
        "intensity": "low",
        "reason": "Luxury voice should breathe minimally and elegantly."
    },

    "mystery": {
        "style": "suspense_reveal_breath",
        "placement": [
            "before_clue",
            "before_hidden_truth",
            "after_disturbing_detail",
            "before_unresolved_question"
        ],
        "base_count": 4,
        "intensity": "medium",
        "reason": "Mystery voice needs breath before clues and unsettling reveals."
    },

    "interior_design": {
        "style": "soft_atmosphere_breath",
        "placement": [
            "after_scene_transition",
            "after_emotional_observation",
            "before_final_reflection"
        ],
        "base_count": 3,
        "intensity": "low",
        "reason": "Interior narration needs soft breathing to create comfort and warmth."
    },

    "finance_simulation": {
        "style": "almost_invisible_analytical_breath",
        "placement": [
            "before_major_conclusion",
            "before_market_reveal",
            "after_section_change"
        ],
        "base_count": 2,
        "intensity": "very_low",
        "reason": "Finance narration should sound professional with almost invisible breaths."
    }
}


INTENSITY_GAIN = {
    "very_low": 0.65,
    "low": 0.80,
    "medium": 1.00,
    "high": 1.20
}


def clamp(value, min_value, max_value):
    return max(
        min_value,
        min(value, max_value)
    )


def estimate_breath_count(
    voice_duration,
    base_count,
    intensity
):
    """
    Voice duration ke hisaab se breath count estimate karta hai.

    Short video:
        45–60 sec → usually 2–5 breaths

    Long video:
        5–10 min → more breaths
    """

    duration = float(voice_duration or 60)

    multiplier = INTENSITY_GAIN.get(
        intensity,
        1.0
    )

    # Base: every 40 seconds approx one natural breath point.
    duration_based = int(duration / 40)

    count = int(
        (base_count + duration_based) * multiplier
    )

    return clamp(
        count,
        1,
        18
    )


def generate_breath_positions(
    voice_duration,
    breath_count
):
    """
    Breath positions ko evenly distribute karta hai.

    Abhi ye timing estimate hai.
    Later script/word timing ke basis par aur smart banega.
    """

    duration = float(voice_duration or 60)

    if breath_count <= 0:
        return []

    positions = []

    segment = duration / (breath_count + 1)

    for i in range(1, breath_count + 1):
        pos = round(
            segment * i,
            2
        )

        positions.append(pos)

    return positions


def build_breath_plan(
    profile,
    voice_duration=60,
    emotion_map=None,
    pause_plan=None
):
    """
    Main function.

    Input:
        profile:
            final profile from voice_master_engine

        voice_duration:
            voice duration in seconds

        emotion_map:
            optional emotion mapper output

        pause_plan:
            optional pause engine output

    Output:
        breath_plan dict
    """

    profile_id = profile.get(
        "profile_id",
        "quantum_future"
    )

    if profile_id not in BREATH_RULES:
        profile_id = "quantum_future"

    rules = BREATH_RULES[profile_id]

    breathing = profile.get(
        "breathing",
        {}
    )

    enabled = bool(
        breathing.get("enabled", True)
    )

    breath_volume_db = float(
        breathing.get("volume_db", -35)
    )

    intensity = rules.get(
        "intensity",
        "low"
    )

    base_count = int(
        rules.get("base_count", 3)
    )

    breath_count = estimate_breath_count(
        voice_duration=voice_duration,
        base_count=base_count,
        intensity=intensity
    )

    if not enabled:
        breath_count = 0

    positions = generate_breath_positions(
        voice_duration=voice_duration,
        breath_count=breath_count
    )

    # If emotion map has many keywords, slightly increase breath intelligence.
    keyword_count = 0

    if emotion_map:
        keyword_count = int(
            emotion_map.get("keyword_count", 0)
        )

    if keyword_count >= 6 and enabled:
        extra_position = round(
            float(voice_duration) * 0.18,
            2
        )

        if extra_position not in positions:
            positions.insert(
                0,
                extra_position
            )

    # Safety breath volume.
    breath_volume_db = clamp(
        breath_volume_db,
        -42,
        -30
    )

    breath_plan = {
        "profile_id": profile_id,
        "enabled": enabled,
        "breath_style": rules.get("style"),
        "intensity": intensity,
        "breath_volume_db": breath_volume_db,
        "estimated_breath_count": len(positions),
        "breath_positions_sec": positions,
        "placement_strategy": rules.get("placement", []),
        "reason": rules.get("reason"),
        "emotion_keyword_count": keyword_count
    }

    return breath_plan


def print_breath_plan(breath_plan):
    print("")
    print("========================================")
    print("VOICE BREATH PLAN")
    print("========================================")
    print("Profile ID:", breath_plan.get("profile_id"))
    print("Enabled:", breath_plan.get("enabled"))
    print("Breath Style:", breath_plan.get("breath_style"))
    print("Intensity:", breath_plan.get("intensity"))
    print("Breath Volume dB:", breath_plan.get("breath_volume_db"))
    print("Estimated Breath Count:", breath_plan.get("estimated_breath_count"))
    print("Breath Positions:", breath_plan.get("breath_positions_sec"))
    print("Placement Strategy:", breath_plan.get("placement_strategy"))
    print("Reason:", breath_plan.get("reason"))
    print("========================================")
    print("")


if __name__ == "__main__":
    from voice_engine.voice_master_engine import (
        build_voice_humanization_profile
    )

    from voice_engine.processing.emotion_mapper import (
        build_emotion_map
    )

    from voice_engine.processing.pause_engine import (
        build_pause_events
    )

    test_script = """
    The system was no longer asking for permission.
    It was evolving.
    And humanity was slowly losing control of the future.
    """

    profile = build_voice_humanization_profile(
        selected_profile="auto",
        content_hint="AI future documentary",
        save_report=False
    )

    emotion_map = build_emotion_map(
        profile_id=profile.get("profile_id"),
        script_text=test_script,
        content_hint="AI future documentary"
    )

    pause_plan = build_pause_events(
        profile=profile,
        script_text=test_script,
        content_hint="AI future documentary",
        emotion_map=emotion_map
    )

    breath_plan = build_breath_plan(
        profile=profile,
        voice_duration=60,
        emotion_map=emotion_map,
        pause_plan=pause_plan
    )

    print_breath_plan(breath_plan)