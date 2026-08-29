"""
EMPHASIS ENGINE
===============

Purpose:
Niche-specific important words ko detect karke
emphasis plan generate karna.

Ye file abhi audio ko direct edit nahi karti.
Ye emphasis map banati hai jo later voice_preprocessor.py use karega.

Goal:
AI voice ko flat robotic delivery se nikal kar
important words par natural human emphasis dena.

Supported niches:
- quantum_future
- stoic_wisdom
- luxury_lifestyle
- mystery
- interior_design
- finance_simulation
"""

import re


EMPHASIS_RULES = {
    "quantum_future": {
        "style": "cinematic_future_emphasis",
        "keywords": {
            "high": [
                "humanity", "control", "future", "machines",
                "evolving", "dangerous", "singularity"
            ],
            "medium": [
                "ai", "system", "technology", "algorithm",
                "automation", "digital", "neural", "data"
            ],
            "soft": [
                "world", "change", "intelligence"
            ]
        },
        "base_boost_db": 1.7
    },

    "stoic_wisdom": {
        "style": "philosophical_weight_emphasis",
        "keywords": {
            "high": [
                "wisdom", "discipline", "self-control",
                "peace", "suffering"
            ],
            "medium": [
                "patience", "ego", "strength", "mind",
                "acceptance"
            ],
            "soft": [
                "life", "silence", "growth", "inner"
            ]
        },
        "base_boost_db": 1.4
    },

    "luxury_lifestyle": {
        "style": "premium_confidence_emphasis",
        "keywords": {
            "high": [
                "luxury", "exclusivity", "freedom",
                "timeless", "sophistication"
            ],
            "medium": [
                "wealth", "privacy", "elegance",
                "craftsmanship", "premium"
            ],
            "soft": [
                "quality", "success", "villa", "mansion"
            ]
        },
        "base_boost_db": 1.4
    },

    "mystery": {
        "style": "suspense_reveal_emphasis",
        "keywords": {
            "high": [
                "secret", "hidden", "truth",
                "disappeared", "unexplained",
                "disturbing"
            ],
            "medium": [
                "unknown", "evidence", "strange",
                "investigation", "mystery", "clue"
            ],
            "soft": [
                "dark", "room", "case", "shadow", "danger"
            ]
        },
        "base_boost_db": 1.8
    },

    "interior_design": {
        "style": "soft_aesthetic_emphasis",
        "keywords": {
            "high": [
                "comfort", "warmth", "harmony",
                "atmosphere", "natural light"
            ],
            "medium": [
                "texture", "calm", "peaceful",
                "balance", "space"
            ],
            "soft": [
                "room", "light", "soft", "cozy", "design"
            ]
        },
        "base_boost_db": 1.2
    },

    "finance_simulation": {
        "style": "strategic_financial_emphasis",
        "keywords": {
            "high": [
                "inflation", "liquidity", "debt",
                "ownership", "valuation", "recession"
            ],
            "medium": [
                "capital", "market", "risk",
                "economy", "financial", "growth"
            ],
            "soft": [
                "asset", "money", "interest",
                "rates", "investors", "banks"
            ]
        },
        "base_boost_db": 1.3
    }
}


LEVEL_MULTIPLIER = {
    "soft": 0.65,
    "medium": 1.00,
    "high": 1.25
}


def clean_text(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keyword_exists(text, keyword):
    text = clean_text(text)
    keyword = clean_text(keyword)

    if not keyword:
        return False

    return keyword in text


def clamp(value, min_value, max_value):
    return max(
        min_value,
        min(value, max_value)
    )


def build_emphasis_plan(
    profile,
    script_text="",
    content_hint="",
    emotion_map=None
):
    """
    Main function.

    Input:
        profile:
            final voice profile from voice_master_engine

        script_text:
            full script if available

        content_hint:
            title/topic/niche hint

        emotion_map:
            optional output from emotion_mapper.py

    Output:
        emphasis_plan dict
    """

    profile_id = profile.get(
        "profile_id",
        "quantum_future"
    )

    if profile_id not in EMPHASIS_RULES:
        profile_id = "quantum_future"

    rules = EMPHASIS_RULES[profile_id]

    combined_text = clean_text(
        f"{content_hint} {script_text}"
    )

    base_boost = float(
        rules.get("base_boost_db", 1.3)
    )

    emotion_strength = 1.0

    if emotion_map:
        emotion_strength = float(
            emotion_map.get("emphasis_strength", 1.0)
        )

    hits = {
        "high": [],
        "medium": [],
        "soft": []
    }

    boost_plan = []

    for level, keywords in rules.get("keywords", {}).items():
        for keyword in keywords:
            if keyword_exists(combined_text, keyword):
                hits[level].append(keyword)

                boost_db = base_boost
                boost_db *= LEVEL_MULTIPLIER.get(level, 1.0)
                boost_db *= emotion_strength

                boost_db = clamp(
                    boost_db,
                    0.6,
                    3.2
                )

                boost_plan.append({
                    "keyword": keyword,
                    "level": level,
                    "boost_db": round(boost_db, 2),
                    "suggested_style": rules.get("style")
                })

    total_hits = (
        len(hits["high"])
        + len(hits["medium"])
        + len(hits["soft"])
    )

    emphasis_plan = {
        "profile_id": profile_id,
        "emphasis_style": rules.get("style"),
        "base_boost_db": base_boost,
        "emotion_strength": emotion_strength,
        "keyword_hits": {
            "high": sorted(set(hits["high"])),
            "medium": sorted(set(hits["medium"])),
            "soft": sorted(set(hits["soft"]))
        },
        "boost_plan": boost_plan,
        "total_emphasis_keywords": total_hits,
        "has_emphasis": total_hits > 0,
        "recommendation": build_recommendation(
            profile_id,
            total_hits,
            hits
        )
    }

    return emphasis_plan


def build_recommendation(
    profile_id,
    total_hits,
    hits
):
    if total_hits == 0:
        return (
            "No strong emphasis keywords detected. Keep voice natural and balanced."
        )

    if hits.get("high"):
        return (
            "Apply stronger but controlled emphasis on high-priority keywords."
        )

    if hits.get("medium"):
        return (
            "Apply medium emphasis on important concepts."
        )

    if profile_id == "finance_simulation":
        return (
            "Use small strategic emphasis without sounding dramatic."
        )

    if profile_id == "interior_design":
        return (
            "Use soft emotional emphasis without breaking calm mood."
        )

    if profile_id == "stoic_wisdom":
        return (
            "Use thoughtful emphasis with slow reflective delivery."
        )

    if profile_id == "mystery":
        return (
            "Use suspenseful emphasis before hidden clues and reveals."
        )

    if profile_id == "luxury_lifestyle":
        return (
            "Use refined emphasis to create premium confidence."
        )

    return (
        "Use cinematic emphasis on future tension and reveal words."
    )


def print_emphasis_plan(emphasis_plan):
    print("")
    print("========================================")
    print("VOICE EMPHASIS PLAN")
    print("========================================")
    print("Profile ID:", emphasis_plan.get("profile_id"))
    print("Emphasis Style:", emphasis_plan.get("emphasis_style"))
    print("Emotion Strength:", emphasis_plan.get("emotion_strength"))
    print("Keyword Hits:", emphasis_plan.get("keyword_hits"))
    print("Total Keywords:", emphasis_plan.get("total_emphasis_keywords"))
    print("Boost Plan:", emphasis_plan.get("boost_plan"))
    print("Recommendation:", emphasis_plan.get("recommendation"))
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

    emphasis_plan = build_emphasis_plan(
        profile=profile,
        script_text=test_script,
        content_hint="AI future documentary",
        emotion_map=emotion_map
    )

    print_emphasis_plan(emphasis_plan)