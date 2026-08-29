"""
HUMAN TIMING ENGINE
===================

Purpose:
Niche ke hisaab se voice rhythm, delivery speed, ending softness,
hook intensity aur reveal pacing ka plan generate karna.

Ye file abhi audio waveform ko direct edit nahi karti.
Ye timing plan banati hai jo later voice_preprocessor.py use karega.

Goal:
AI voice ko same-speed robotic narration se nikal kar
human-style dynamic delivery dena.
"""


TIMING_RULES = {
    "quantum_future": {
        "style": "netflix_future_documentary_timing",
        "hook_speed_multiplier": 0.96,
        "middle_speed_multiplier": 1.00,
        "reveal_speed_multiplier": 0.92,
        "ending_speed_multiplier": 0.90,
        "hook_energy": "controlled_tension",
        "ending_delivery": "soft_philosophical",
        "reason": "Future documentary voice needs slow cinematic tension and stronger reveal pacing."
    },

    "stoic_wisdom": {
        "style": "wise_philosopher_timing",
        "hook_speed_multiplier": 0.94,
        "middle_speed_multiplier": 0.97,
        "reveal_speed_multiplier": 0.90,
        "ending_speed_multiplier": 0.88,
        "hook_energy": "quiet_observation",
        "ending_delivery": "reflective_soft",
        "reason": "Stoic wisdom voice needs slower reflective rhythm and meaningful silence."
    },

    "luxury_lifestyle": {
        "style": "premium_luxury_timing",
        "hook_speed_multiplier": 0.96,
        "middle_speed_multiplier": 0.98,
        "reveal_speed_multiplier": 0.94,
        "ending_speed_multiplier": 0.92,
        "hook_energy": "calm_confidence",
        "ending_delivery": "quiet_authority",
        "reason": "Luxury narration should feel effortless, slow and refined."
    },

    "mystery": {
        "style": "suspense_documentary_timing",
        "hook_speed_multiplier": 0.93,
        "middle_speed_multiplier": 0.97,
        "reveal_speed_multiplier": 0.88,
        "ending_speed_multiplier": 0.86,
        "hook_energy": "controlled_suspense",
        "ending_delivery": "unresolved_soft",
        "reason": "Mystery narration needs delayed information and slow reveal pacing."
    },

    "interior_design": {
        "style": "calm_aesthetic_timing",
        "hook_speed_multiplier": 0.95,
        "middle_speed_multiplier": 0.96,
        "reveal_speed_multiplier": 0.93,
        "ending_speed_multiplier": 0.90,
        "hook_energy": "soft_welcome",
        "ending_delivery": "warm_comforting",
        "reason": "Interior narration needs relaxed breathing space and warm pacing."
    },

    "finance_simulation": {
        "style": "analytical_financial_timing",
        "hook_speed_multiplier": 0.98,
        "middle_speed_multiplier": 1.00,
        "reveal_speed_multiplier": 0.95,
        "ending_speed_multiplier": 0.93,
        "hook_energy": "strategic_observation",
        "ending_delivery": "confident_reflection",
        "reason": "Finance narration should stay efficient but slow slightly for important implications."
    }
}


def clamp(value, min_value, max_value):
    return max(
        min_value,
        min(value, max_value)
    )


def build_timing_plan(
    profile,
    voice_duration=60,
    emotion_map=None,
    pause_plan=None,
    breath_plan=None,
    emphasis_plan=None
):
    """
    Main function.

    Input:
        profile:
            Final voice profile from voice_master_engine

        voice_duration:
            voice duration in seconds

        emotion_map / pause_plan / breath_plan / emphasis_plan:
            Optional intelligence maps

    Output:
        timing_plan dict
    """

    profile_id = profile.get(
        "profile_id",
        "quantum_future"
    )

    if profile_id not in TIMING_RULES:
        profile_id = "quantum_future"

    rules = TIMING_RULES[profile_id]

    voice = profile.get(
        "voice",
        {}
    )

    base_speed = float(
        voice.get("speed", 0.92)
    )

    keyword_count = 0
    emphasis_count = 0
    pause_keywords = 0
    breath_count = 0

    if emotion_map:
        keyword_count = int(
            emotion_map.get("keyword_count", 0)
        )

    if emphasis_plan:
        emphasis_count = int(
            emphasis_plan.get("total_emphasis_keywords", 0)
        )

    if pause_plan:
        pause_keywords = int(
            pause_plan.get("total_pause_keywords", 0)
        )

    if breath_plan:
        breath_count = int(
            breath_plan.get("estimated_breath_count", 0)
        )

    intensity_score = (
        keyword_count
        + emphasis_count
        + pause_keywords
        + breath_count
    )

    if intensity_score >= 18:
        delivery_intensity = "high"
    elif intensity_score >= 9:
        delivery_intensity = "medium"
    else:
        delivery_intensity = "low"

    hook_speed = base_speed * float(
        rules.get("hook_speed_multiplier", 0.96)
    )

    middle_speed = base_speed * float(
        rules.get("middle_speed_multiplier", 1.00)
    )

    reveal_speed = base_speed * float(
        rules.get("reveal_speed_multiplier", 0.92)
    )

    ending_speed = base_speed * float(
        rules.get("ending_speed_multiplier", 0.90)
    )

    hook_speed = round(
        clamp(hook_speed, 0.82, 1.00),
        3
    )

    middle_speed = round(
        clamp(middle_speed, 0.84, 1.02),
        3
    )

    reveal_speed = round(
        clamp(reveal_speed, 0.78, 0.98),
        3
    )

    ending_speed = round(
        clamp(ending_speed, 0.76, 0.96),
        3
    )

    duration = float(voice_duration or 60)

    sections = {
        "hook": {
            "start": 0.0,
            "end": round(duration * 0.18, 2),
            "speed": hook_speed,
            "energy": rules.get("hook_energy")
        },
        "middle": {
            "start": round(duration * 0.18, 2),
            "end": round(duration * 0.78, 2),
            "speed": middle_speed,
            "energy": "balanced_narration"
        },
        "reveal": {
            "start": round(duration * 0.78, 2),
            "end": round(duration * 0.92, 2),
            "speed": reveal_speed,
            "energy": "slower_reveal"
        },
        "ending": {
            "start": round(duration * 0.92, 2),
            "end": round(duration, 2),
            "speed": ending_speed,
            "energy": rules.get("ending_delivery")
        }
    }

    timing_plan = {
        "profile_id": profile_id,
        "timing_style": rules.get("style"),
        "base_speed": base_speed,
        "delivery_intensity": delivery_intensity,
        "intelligence_counts": {
            "emotion_keywords": keyword_count,
            "emphasis_keywords": emphasis_count,
            "pause_keywords": pause_keywords,
            "breath_count": breath_count,
            "total_intensity_score": intensity_score
        },
        "section_timing": sections,
        "recommended_speed_curve": [
            {
                "section": "hook",
                "speed": hook_speed
            },
            {
                "section": "middle",
                "speed": middle_speed
            },
            {
                "section": "reveal",
                "speed": reveal_speed
            },
            {
                "section": "ending",
                "speed": ending_speed
            }
        ],
        "reason": rules.get("reason")
    }

    return timing_plan


def print_timing_plan(timing_plan):
    print("")
    print("========================================")
    print("VOICE HUMAN TIMING PLAN")
    print("========================================")
    print("Profile ID:", timing_plan.get("profile_id"))
    print("Timing Style:", timing_plan.get("timing_style"))
    print("Base Speed:", timing_plan.get("base_speed"))
    print("Delivery Intensity:", timing_plan.get("delivery_intensity"))
    print("Counts:", timing_plan.get("intelligence_counts"))
    print("Speed Curve:", timing_plan.get("recommended_speed_curve"))
    print("Reason:", timing_plan.get("reason"))
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

    from voice_engine.processing.breath_engine import (
        build_breath_plan
    )

    from voice_engine.processing.emphasis_engine import (
        build_emphasis_plan
    )

    test_script = """
    The system was no longer asking for permission.
    It was evolving.
    Humanity was slowly losing control of the future.
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

    emphasis_plan = build_emphasis_plan(
        profile=profile,
        script_text=test_script,
        content_hint="AI future documentary",
        emotion_map=emotion_map
    )

    timing_plan = build_timing_plan(
        profile=profile,
        voice_duration=60,
        emotion_map=emotion_map,
        pause_plan=pause_plan,
        breath_plan=breath_plan,
        emphasis_plan=emphasis_plan
    )

    print_timing_plan(timing_plan)