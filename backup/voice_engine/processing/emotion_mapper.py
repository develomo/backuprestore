"""
EMOTION MAPPER
==============

Purpose:
Script / topic / content hint ko analyze karke niche ke hisaab se
important emotional keywords detect karna.

Ye file audio process nahi karti.
Ye sirf emotion map banati hai.

Later:
voice_preprocessor.py is emotion map ko use karega
taake important words par emphasis / pause / breath logic apply ho sake.
"""

import re


NICHE_KEYWORDS = {
    "quantum_future": {
        "emotion": "cinematic_future_tension",
        "keywords": [
            "ai", "artificial intelligence", "future", "machine",
            "machines", "control", "humanity", "automation",
            "system", "technology", "singularity", "algorithm",
            "robots", "digital", "evolving", "dangerous",
            "intelligence", "neural", "data"
        ],
        "emphasis_strength": 1.7,
        "pause_strength": 1.3
    },

    "stoic_wisdom": {
        "emotion": "calm_philosophical_reflection",
        "keywords": [
            "wisdom", "discipline", "patience", "ego",
            "peace", "suffering", "strength", "self-control",
            "silence", "mind", "life", "pain",
            "growth", "acceptance", "control", "inner"
        ],
        "emphasis_strength": 1.4,
        "pause_strength": 1.6
    },

    "luxury_lifestyle": {
        "emotion": "premium_refined_confidence",
        "keywords": [
            "luxury", "exclusive", "exclusivity", "private",
            "privacy", "wealth", "freedom", "elegance",
            "timeless", "quality", "success", "sophistication",
            "premium", "villa", "mansion", "craftsmanship"
        ],
        "emphasis_strength": 1.4,
        "pause_strength": 1.3
    },

    "mystery": {
        "emotion": "suspense_hidden_truth",
        "keywords": [
            "secret", "hidden", "unknown", "truth",
            "evidence", "disappeared", "strange", "unexplained",
            "discovered", "investigation", "mystery",
            "dark", "room", "case", "clue", "shadow",
            "danger", "disturbing"
        ],
        "emphasis_strength": 1.8,
        "pause_strength": 1.8
    },

    "interior_design": {
        "emotion": "warm_soft_aesthetic",
        "keywords": [
            "comfort", "warmth", "harmony", "light",
            "natural light", "texture", "calm", "atmosphere",
            "space", "room", "soft", "peaceful",
            "cozy", "design", "balance", "relaxing"
        ],
        "emphasis_strength": 1.2,
        "pause_strength": 1.4
    },

    "finance_simulation": {
        "emotion": "analytical_financial_authority",
        "keywords": [
            "inflation", "debt", "capital", "ownership",
            "liquidity", "market", "risk", "valuation",
            "recession", "growth", "economy", "financial",
            "asset", "money", "interest", "rates",
            "investors", "banks", "wealth"
        ],
        "emphasis_strength": 1.3,
        "pause_strength": 1.2
    }
}


def clean_text(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_keyword_hits(text, keywords):
    cleaned = clean_text(text)
    hits = []

    for keyword in keywords:
        key = clean_text(keyword)

        if not key:
            continue

        if key in cleaned:
            hits.append(keyword)

    return sorted(set(hits))


def build_emotion_map(profile_id, script_text="", content_hint=""):
    """
    Main function.

    Input:
        profile_id:
            quantum_future / mystery / finance_simulation etc.

        script_text:
            Full script if available.

        content_hint:
            Title / topic / niche hint.

    Output:
        emotion_map dict
    """

    profile_id = str(profile_id or "quantum_future").strip()

    if profile_id not in NICHE_KEYWORDS:
        profile_id = "quantum_future"

    data = NICHE_KEYWORDS[profile_id]

    combined_text = f"{content_hint} {script_text}"

    keyword_hits = find_keyword_hits(
        combined_text,
        data.get("keywords", [])
    )

    emotion_map = {
        "profile_id": profile_id,
        "emotion": data.get("emotion", "neutral_documentary"),
        "keyword_hits": keyword_hits,
        "keyword_count": len(keyword_hits),
        "emphasis_strength": data.get("emphasis_strength", 1.0),
        "pause_strength": data.get("pause_strength", 1.0),
        "has_emotional_keywords": len(keyword_hits) > 0
    }

    return emotion_map


def print_emotion_map(emotion_map):
    print("")
    print("========================================")
    print("VOICE EMOTION MAP")
    print("========================================")
    print("Profile ID:", emotion_map.get("profile_id"))
    print("Emotion:", emotion_map.get("emotion"))
    print("Keyword Count:", emotion_map.get("keyword_count"))
    print("Keyword Hits:", emotion_map.get("keyword_hits"))
    print("Emphasis Strength:", emotion_map.get("emphasis_strength"))
    print("Pause Strength:", emotion_map.get("pause_strength"))
    print("========================================")
    print("")


if __name__ == "__main__":
    test = build_emotion_map(
        profile_id="quantum_future",
        content_hint="AI machines may control the future of humanity",
        script_text="The system was no longer asking for permission. It was evolving."
    )

    print_emotion_map(test)