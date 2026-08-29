"""
PAUSE ENGINE
============

Purpose:
Niche-specific pause intelligence generate karna.

Ye file audio ko abhi direct edit nahi karti.
Ye pause map banati hai jo later voice_preprocessor.py use karega.

Goal:
AI voice ko robotic continuous speaking se nikal kar
human-like thoughtful narration me convert karna.

Supported niches:
- quantum_future
- stoic_wisdom
- luxury_lifestyle
- mystery
- interior_design
- finance_simulation
"""

import re


PAUSE_KEYWORDS = {
    "quantum_future": {
        "short_pause_words": [
            "ai", "system", "data", "future"
        ],
        "medium_pause_words": [
            "humanity", "machine", "machines", "technology", "algorithm"
        ],
        "long_pause_words": [
            "control", "evolving", "dangerous", "permission", "singularity"
        ],
        "style": "cinematic_future_pause"
    },

    "stoic_wisdom": {
        "short_pause_words": [
            "life", "mind", "peace"
        ],
        "medium_pause_words": [
            "discipline", "patience", "ego", "strength"
        ],
        "long_pause_words": [
            "wisdom", "suffering", "self-control", "acceptance"
        ],
        "style": "philosophical_reflection_pause"
    },

    "luxury_lifestyle": {
        "short_pause_words": [
            "luxury", "quality", "success"
        ],
        "medium_pause_words": [
            "elegance", "freedom", "privacy", "premium"
        ],
        "long_pause_words": [
            "exclusivity", "timeless", "sophistication", "craftsmanship"
        ],
        "style": "elegant_premium_pause"
    },

    "mystery": {
        "short_pause_words": [
            "strange", "dark", "clue"
        ],
        "medium_pause_words": [
            "secret", "hidden", "unknown", "evidence"
        ],
        "long_pause_words": [
            "disappeared", "truth", "unexplained", "disturbing", "investigation"
        ],
        "style": "suspense_reveal_pause"
    },

    "interior_design": {
        "short_pause_words": [
            "room", "space", "light"
        ],
        "medium_pause_words": [
            "comfort", "warmth", "texture", "balance"
        ],
        "long_pause_words": [
            "harmony", "atmosphere", "peaceful", "natural light"
        ],
        "style": "soft_atmosphere_pause"
    },

    "finance_simulation": {
        "short_pause_words": [
            "market", "money", "risk"
        ],
        "medium_pause_words": [
            "inflation", "debt", "capital", "growth"
        ],
        "long_pause_words": [
            "liquidity", "ownership", "valuation", "recession", "economy"
        ],
        "style": "analytical_strategy_pause"
    }
}


def clean_text(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_keyword(text, keyword):
    text = clean_text(text)
    keyword = clean_text(keyword)

    if not keyword:
        return False

    return keyword in text


def build_pause_events(
    profile,
    script_text="",
    content_hint="",
    emotion_map=None
):
    """
    Main function.

    Input:
        profile:
            Final voice profile from voice_master_engine.

        script_text:
            Full script if available.

        content_hint:
            Video topic/title/niche hint.

        emotion_map:
            Optional output from emotion_mapper.py.

    Output:
        pause_plan dict
    """

    profile_id = profile.get(
        "profile_id",
        "quantum_future"
    )

    if profile_id not in PAUSE_KEYWORDS:
        profile_id = "quantum_future"

    pauses = profile.get("pauses", {})

    comma_pause = float(pauses.get("comma", 0.20))
    thinking_pause = float(pauses.get("thinking", 0.70))
    dramatic_pause = float(pauses.get("dramatic", 1.00))
    reveal_pause = float(pauses.get("reveal", 1.20))

    pause_strength = 1.0

    if emotion_map:
        pause_strength = float(
            emotion_map.get("pause_strength", 1.0)
        )

    data = PAUSE_KEYWORDS[profile_id]

    combined_text = clean_text(
        f"{content_hint} {script_text}"
    )

    short_hits = []
    medium_hits = []
    long_hits = []

    for word in data.get("short_pause_words", []):
        if contains_keyword(combined_text, word):
            short_hits.append(word)

    for word in data.get("medium_pause_words", []):
        if contains_keyword(combined_text, word):
            medium_hits.append(word)

    for word in data.get("long_pause_words", []):
        if contains_keyword(combined_text, word):
            long_hits.append(word)

    short_pause = round(
        comma_pause * pause_strength,
        3
    )

    medium_pause = round(
        thinking_pause * pause_strength,
        3
    )

    long_pause = round(
        reveal_pause * pause_strength,
        3
    )

    # Safety limits:
    # Human pauses should not become absurdly long.
    short_pause = clamp(
        short_pause,
        0.12,
        0.35
    )

    medium_pause = clamp(
        medium_pause,
        0.45,
        1.35
    )

    long_pause = clamp(
        long_pause,
        0.85,
        2.10
    )

    pause_plan = {
        "profile_id": profile_id,
        "pause_style": data.get("style"),
        "pause_strength": pause_strength,

        "base_pauses": {
            "comma": comma_pause,
            "thinking": thinking_pause,
            "dramatic": dramatic_pause,
            "reveal": reveal_pause
        },

        "computed_pauses": {
            "short_pause": short_pause,
            "medium_pause": medium_pause,
            "long_pause": long_pause
        },

        "keyword_hits": {
            "short": sorted(set(short_hits)),
            "medium": sorted(set(medium_hits)),
            "long": sorted(set(long_hits))
        },

        "total_pause_keywords": (
            len(short_hits)
            + len(medium_hits)
            + len(long_hits)
        ),

        "recommendation": build_pause_recommendation(
            profile_id,
            short_hits,
            medium_hits,
            long_hits
        )
    }

    return pause_plan


def build_pause_recommendation(
    profile_id,
    short_hits,
    medium_hits,
    long_hits
):
    """
    Human-readable recommendation.
    Useful for UI logs/debug.
    """

    if long_hits:
        return (
            "Use longer emotional/reveal pauses around major keywords."
        )

    if medium_hits:
        return (
            "Use medium reflective pauses around important concepts."
        )

    if short_hits:
        return (
            "Use light natural pauses to avoid robotic continuous delivery."
        )

    if profile_id == "finance_simulation":
        return (
            "Use measured analytical pauses after data-heavy lines."
        )

    if profile_id == "interior_design":
        return (
            "Use soft atmosphere pauses to let the space feel calm."
        )

    if profile_id == "stoic_wisdom":
        return (
            "Use reflective pauses after meaningful observations."
        )

    if profile_id == "mystery":
        return (
            "Use suspense pauses before clues and reveals."
        )

    if profile_id == "luxury_lifestyle":
        return (
            "Use elegant pauses to create premium confidence."
        )

    return (
        "Use cinematic pauses around future tension and reveal moments."
    )


def clamp(value, min_value, max_value):
    return max(
        min_value,
        min(value, max_value)
    )


def print_pause_plan(pause_plan):
    print("")
    print("========================================")
    print("VOICE PAUSE PLAN")
    print("========================================")
    print("Profile ID:", pause_plan.get("profile_id"))
    print("Pause Style:", pause_plan.get("pause_style"))
    print("Pause Strength:", pause_plan.get("pause_strength"))
    print("Computed Pauses:", pause_plan.get("computed_pauses"))
    print("Keyword Hits:", pause_plan.get("keyword_hits"))
    print("Total Pause Keywords:", pause_plan.get("total_pause_keywords"))
    print("Recommendation:", pause_plan.get("recommendation"))
    print("========================================")
    print("")


if __name__ == "__main__":
    from voice_engine.voice_master_engine import (
        build_voice_humanization_profile
    )

    from voice_engine.processing.emotion_mapper import (
        build_emotion_map
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

    print_pause_plan(pause_plan)