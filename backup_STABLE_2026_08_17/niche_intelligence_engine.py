# niche_intelligence_engine.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# NICHE INTELLIGENCE ENGINE v1.0
# ==========================================================
# Purpose:
# - Supports fixed niches and unlimited/auto custom niches.
# - Understands niche meaning using keyword families.
# - Converts any niche/script into a professional editing DNA.
# - Keeps effects minimal, premium, and clip-quality safe.
# - Avoids using the same color/effects/motion style for all niches.
#
# Design:
# This engine does NOT use any paid API.
# It runs locally using rules, semantic keyword families,
# weighted scoring, and safe defaults.
# ==========================================================

import re
import math
from copy import deepcopy


# ==========================================================
# SUPPORTED FIXED NICHES
# ==========================================================

FIXED_NICHES = {
    "quantum_future",
    "stoic_wisdom",
    "luxury_lifestyle",
    "mystery",
    "interior_design",
    "finance_simulation",
}

DEFAULT_NICHE = "auto_general"


# ==========================================================
# CORE STYLE FAMILIES
# ==========================================================
# These families allow Auto mode to support 1000+ niches.
# Example:
# "luxury watches" -> luxury + product + cinematic
# "AI robots future" -> future_tech + science + high_energy
# "dark mystery case" -> mystery + dark_documentary
# ==========================================================

STYLE_FAMILIES = {
    "future_tech": {
        "keywords": {
            "ai", "artificial intelligence", "robot", "robots", "future",
            "technology", "quantum", "machine", "automation", "neural",
            "cyber", "space", "science", "scientist", "innovation",
            "breakthrough", "digital", "software", "algorithm", "data",
            "internet", "metaverse", "virtual", "simulation",
        },
        "energy": 0.78,
        "motion": "precise_dynamic",
        "color_family": "cool_cyan_blue",
        "voice_family": "energetic_clear",
        "caption_family": "future_clean",
        "transition_family": "clean_tech",
    },

    "luxury": {
        "keywords": {
            "luxury", "rich", "wealth", "wealthy", "billionaire",
            "millionaire", "mansion", "villa", "yacht", "private jet",
            "jet", "supercar", "watch", "watches", "diamond", "gold",
            "premium", "elite", "exclusive", "lifestyle", "royal",
            "hotel", "resort", "fashion", "brand", "expensive",
        },
        "energy": 0.62,
        "motion": "smooth_cinematic",
        "color_family": "warm_gold_champagne",
        "voice_family": "warm_measured",
        "caption_family": "premium_luxury",
        "transition_family": "soft_cinematic",
    },

    "mystery": {
        "keywords": {
            "mystery", "secret", "hidden", "dark", "unknown", "case",
            "crime", "conspiracy", "truth", "buried", "forbidden",
            "haunted", "ghost", "fear", "danger", "warning", "creepy",
            "evidence", "lost", "missing", "strange", "unexplained",
            "ancient secret", "classified",
        },
        "energy": 0.72,
        "motion": "tense_controlled",
        "color_family": "cool_shadow_violet",
        "voice_family": "dramatic_tense",
        "caption_family": "mystery_contrast",
        "transition_family": "tension_cut",
    },

    "wisdom": {
        "keywords": {
            "wisdom", "stoic", "stoicism", "mindset", "discipline",
            "life lesson", "philosophy", "ancient", "peace", "control",
            "patience", "silence", "growth", "meaning", "truth",
            "emotional control", "habits", "self improvement",
            "motivation", "mental strength", "calm",
        },
        "energy": 0.45,
        "motion": "slow_reflective",
        "color_family": "neutral_warm_soft",
        "voice_family": "calm_deliberate",
        "caption_family": "documentary_clean",
        "transition_family": "gentle_fade",
    },

    "interior_design": {
        "keywords": {
            "interior", "design", "room", "home", "house", "decor",
            "architecture", "space", "living room", "bedroom", "kitchen",
            "minimal", "aesthetic", "cozy", "modern", "renovation",
            "before after", "transformation", "furniture", "lighting",
            "wall", "studio apartment",
        },
        "energy": 0.52,
        "motion": "soft_aesthetic",
        "color_family": "natural_warm_clean",
        "voice_family": "clean_aesthetic",
        "caption_family": "aesthetic_soft",
        "transition_family": "smooth_gallery",
    },

    "finance": {
        "keywords": {
            "finance", "money", "invest", "investment", "stock",
            "stocks", "trading", "crypto", "business", "income",
            "profit", "loss", "saving", "wealth building", "cash",
            "market", "economy", "bank", "budget", "tax", "asset",
            "debt", "financial freedom", "compound",
        },
        "energy": 0.66,
        "motion": "clean_decisive",
        "color_family": "emerald_blue_clean",
        "voice_family": "sharp_decisive",
        "caption_family": "business_clear",
        "transition_family": "sharp_clean",
    },

    "documentary": {
        "keywords": {
            "documentary", "history", "story", "explained", "timeline",
            "rise", "fall", "empire", "war", "society", "culture",
            "country", "civilization", "human", "people", "world",
            "investigation", "real story", "behind the scenes",
        },
        "energy": 0.58,
        "motion": "documentary_drift",
        "color_family": "natural_documentary",
        "voice_family": "warm_measured",
        "caption_family": "documentary_clean",
        "transition_family": "smooth_documentary",
    },

    "horror_dark": {
        "keywords": {
            "horror", "scary", "fear", "nightmare", "demon", "evil",
            "darkness", "blood", "monster", "shadow", "haunted",
            "paranormal", "terror", "scream",
        },
        "energy": 0.70,
        "motion": "dark_tension",
        "color_family": "low_key_violet_blue",
        "voice_family": "dramatic_tense",
        "caption_family": "mystery_contrast",
        "transition_family": "dark_cut",
    },

    "education": {
        "keywords": {
            "learn", "education", "tutorial", "how to", "guide",
            "explain", "tips", "tricks", "facts", "lesson",
            "course", "skill", "training", "step by step",
        },
        "energy": 0.56,
        "motion": "clean_teaching",
        "color_family": "neutral_clean_blue",
        "voice_family": "energetic_clear",
        "caption_family": "business_clear",
        "transition_family": "clean_cut",
    },

    "health_wellness": {
        "keywords": {
            "health", "fitness", "wellness", "body", "mind", "sleep",
            "diet", "nutrition", "exercise", "workout", "mental health",
            "stress", "healing", "doctor", "medicine", "healthy",
        },
        "energy": 0.54,
        "motion": "soft_clean",
        "color_family": "natural_green_soft",
        "voice_family": "clean_aesthetic",
        "caption_family": "aesthetic_soft",
        "transition_family": "gentle_clean",
    },
}


# ==========================================================
# FIXED NICHE -> FAMILY MAP
# ==========================================================

FIXED_NICHE_TO_FAMILY = {
    "quantum_future": "future_tech",
    "stoic_wisdom": "wisdom",
    "luxury_lifestyle": "luxury",
    "mystery": "mystery",
    "interior_design": "interior_design",
    "finance_simulation": "finance",
}


# ==========================================================
# SAFE INTENSITY RANGES
# ==========================================================
# These ranges are intentionally conservative.
# User wants original AI clips preserved:
# - no harsh shadows
# - no over-sharpness
# - no aggressive colors
# - no overexposure
# - minimal professional enhancement only
# ==========================================================

SAFE_GLOBAL_LIMITS = {
    "brightness_shift": (-0.025, 0.025),
    "contrast": (0.96, 1.06),
    "saturation": (0.94, 1.08),
    "sharpness": (0.00, 0.16),
    "highlight_protection": (0.06, 0.22),
    "shadow_lift": (0.00, 0.06),
    "vignette": (0.00, 0.05),
    "grain": (0.00, 0.018),
    "bloom": (0.00, 0.08),
    "light_leak": (0.00, 0.05),
    "zoom": (1.015, 1.085),
    "motion_intensity": (0.70, 1.65),
    "transition_seconds": (0.10, 0.34),
    "music_volume": (0.08, 0.22),
    "sfx_volume": (0.04, 0.16),
    "voice_gain": (1.00, 1.18),
}


# ==========================================================
# COLOR FAMILIES
# ==========================================================
# Values are not meant as heavy color grade.
# They are soft direction hints for the color engine.
# ==========================================================

COLOR_FAMILIES = {
    "cool_cyan_blue": {
        "primary": (34, 211, 238),
        "secondary": (59, 130, 246),
        "temperature": -0.04,
        "tint": 0.02,
        "saturation_bias": 1.02,
        "contrast_bias": 1.02,
    },
    "warm_gold_champagne": {
        "primary": (245, 214, 135),
        "secondary": (255, 196, 87),
        "temperature": 0.04,
        "tint": 0.00,
        "saturation_bias": 1.03,
        "contrast_bias": 1.02,
    },
    "cool_shadow_violet": {
        "primary": (168, 85, 247),
        "secondary": (125, 211, 252),
        "temperature": -0.03,
        "tint": 0.03,
        "saturation_bias": 0.98,
        "contrast_bias": 1.03,
    },
    "neutral_warm_soft": {
        "primary": (255, 247, 237),
        "secondary": (245, 214, 135),
        "temperature": 0.025,
        "tint": 0.00,
        "saturation_bias": 0.98,
        "contrast_bias": 0.99,
    },
    "natural_warm_clean": {
        "primary": (255, 247, 237),
        "secondary": (229, 231, 235),
        "temperature": 0.02,
        "tint": -0.01,
        "saturation_bias": 1.00,
        "contrast_bias": 1.00,
    },
    "emerald_blue_clean": {
        "primary": (52, 211, 153),
        "secondary": (96, 165, 250),
        "temperature": -0.01,
        "tint": 0.00,
        "saturation_bias": 1.01,
        "contrast_bias": 1.03,
    },
    "natural_documentary": {
        "primary": (248, 250, 252),
        "secondary": (156, 163, 175),
        "temperature": 0.00,
        "tint": 0.00,
        "saturation_bias": 0.99,
        "contrast_bias": 1.01,
    },
    "low_key_violet_blue": {
        "primary": (129, 140, 248),
        "secondary": (168, 85, 247),
        "temperature": -0.04,
        "tint": 0.04,
        "saturation_bias": 0.96,
        "contrast_bias": 1.04,
    },
    "neutral_clean_blue": {
        "primary": (96, 165, 250),
        "secondary": (248, 250, 252),
        "temperature": -0.01,
        "tint": 0.00,
        "saturation_bias": 1.00,
        "contrast_bias": 1.01,
    },
    "natural_green_soft": {
        "primary": (110, 231, 183),
        "secondary": (255, 247, 237),
        "temperature": 0.01,
        "tint": -0.02,
        "saturation_bias": 0.99,
        "contrast_bias": 0.99,
    },
}


# ==========================================================
# HELPERS
# ==========================================================

def _clean_text(value):
    text = str(value or "").lower()
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9\s\-']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(value):
    text = _clean_text(value)
    if not text:
        return []
    return text.split()


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))


def _score_keyword_family(text, family_keywords):
    """
    Scores a family using both phrase matches and word matches.
    """
    text = _clean_text(text)
    tokens = set(_tokenize(text))

    score = 0.0

    for kw in family_keywords:
        kw_clean = _clean_text(kw)
        if not kw_clean:
            continue

        if " " in kw_clean:
            if kw_clean in text:
                score += 3.0 + min(len(kw_clean.split()) * 0.5, 2.0)
        else:
            if kw_clean in tokens:
                score += 1.5

    return score


def _normalize_scores(scores):
    total = sum(max(v, 0.0) for v in scores.values())
    if total <= 0:
        return {k: 0.0 for k in scores}
    return {k: max(v, 0.0) / total for k, v in scores.items()}


def _estimate_script_energy(script_text):
    """
    Estimates energy from punctuation and intense words.
    """
    text = str(script_text or "")
    clean = _clean_text(text)

    if not clean:
        return 0.55

    intense_words = {
        "shocking", "secret", "danger", "warning", "impossible",
        "never", "now", "fast", "power", "fear", "rich",
        "million", "billion", "breakthrough", "truth", "hidden",
        "changed", "destroyed", "created", "future",
    }

    tokens = _tokenize(clean)
    intense_count = sum(1 for t in tokens if t in intense_words)

    exclamations = text.count("!")
    questions = text.count("?")

    length_factor = min(len(tokens) / 180.0, 1.0)
    intensity = 0.45
    intensity += min(intense_count * 0.025, 0.18)
    intensity += min(exclamations * 0.025, 0.12)
    intensity += min(questions * 0.015, 0.08)
    intensity += length_factor * 0.06

    return _clamp(intensity, 0.35, 0.82)


def _resolve_fixed_niche_family(niche):
    key = str(niche or "").strip().lower()
    return FIXED_NICHE_TO_FAMILY.get(key)


def _family_to_profile(family_key):
    family = STYLE_FAMILIES.get(family_key)
    if not family:
        family = STYLE_FAMILIES["documentary"]

    color_family_key = family.get("color_family", "natural_documentary")
    color_family = COLOR_FAMILIES.get(color_family_key, COLOR_FAMILIES["natural_documentary"])

    return {
        "family_key": family_key,
        "energy": family.get("energy", 0.55),
        "motion_family": family.get("motion", "documentary_drift"),
        "color_family_key": color_family_key,
        "color_family": deepcopy(color_family),
        "voice_family": family.get("voice_family", "warm_measured"),
        "caption_family": family.get("caption_family", "documentary_clean"),
        "transition_family": family.get("transition_family", "smooth_documentary"),
    }


# ==========================================================
# MAIN ANALYSIS
# ==========================================================

def analyze_niche(niche_name=None, script_text=None, mode="short"):
    """
    Converts niche + optional script into an editing DNA profile.

    Args:
        niche_name: string selected/typed niche.
        script_text: optional script/transcript.
        mode: "short" or "long"

    Returns:
        dict containing full niche intelligence profile.
    """
    niche_clean = _clean_text(niche_name)
    script_clean = _clean_text(script_text)

    combined = " ".join([niche_clean, script_clean]).strip()

    fixed_family = _resolve_fixed_niche_family(niche_name)

    raw_scores = {}
    for family_key, family_data in STYLE_FAMILIES.items():
        score = _score_keyword_family(combined, family_data["keywords"])
        raw_scores[family_key] = score

    if fixed_family:
        raw_scores[fixed_family] = raw_scores.get(fixed_family, 0.0) + 8.0

    normalized = _normalize_scores(raw_scores)

    if fixed_family:
        primary_family = fixed_family
    else:
        primary_family = max(raw_scores, key=lambda k: raw_scores[k]) if raw_scores else "documentary"
        if raw_scores.get(primary_family, 0) <= 0:
            primary_family = "documentary"

    # Secondary family helps Auto mode become more specific.
    sorted_families = sorted(
        normalized.items(),
        key=lambda item: item[1],
        reverse=True
    )
    secondary_family = None
    for fam, score in sorted_families:
        if fam != primary_family and score >= 0.12:
            secondary_family = fam
            break

    profile = _family_to_profile(primary_family)

    script_energy = _estimate_script_energy(script_text)
    base_energy = profile["energy"]

    if mode == "long":
        final_energy = base_energy * 0.72 + script_energy * 0.28
        final_energy = _clamp(final_energy, 0.38, 0.72)
    else:
        final_energy = base_energy * 0.62 + script_energy * 0.38
        final_energy = _clamp(final_energy, 0.42, 0.86)

    profile["energy"] = final_energy

    # Confidence based on top family score.
    top_score = raw_scores.get(primary_family, 0.0)
    confidence = _clamp(top_score / 10.0, 0.10, 1.00)

    if fixed_family:
        confidence = max(confidence, 0.82)

    result = {
        "niche_name": str(niche_name or "auto").strip() or "auto",
        "mode": str(mode or "short").lower(),
        "is_fixed_niche": bool(fixed_family),
        "primary_family": primary_family,
        "secondary_family": secondary_family,
        "confidence": confidence,
        "family_scores": normalized,
        "editing_dna": profile,
        "safe_limits": deepcopy(SAFE_GLOBAL_LIMITS),
        "recommendations": build_recommendations(profile, mode=mode),
    }

    return result


# ==========================================================
# RECOMMENDATION BUILDER
# ==========================================================

def build_recommendations(profile, mode="short"):
    """
    Turns family profile into safe recommended ranges.
    """
    energy = _safe_float(profile.get("energy"), 0.55)
    color = profile.get("color_family", COLOR_FAMILIES["natural_documentary"])

    # Motion:
    if mode == "long":
        motion_base = 0.75 + energy * 0.45
    else:
        motion_base = 0.90 + energy * 0.70

    motion_intensity = _clamp(
        motion_base,
        SAFE_GLOBAL_LIMITS["motion_intensity"][0],
        SAFE_GLOBAL_LIMITS["motion_intensity"][1],
    )

    # Cut pacing:
    if mode == "long":
        min_cut = _clamp(3.2 - energy * 0.8, 2.4, 4.2)
        max_cut = _clamp(6.8 - energy * 1.2, 4.2, 7.8)
    else:
        min_cut = _clamp(2.4 - energy * 0.9, 1.2, 2.8)
        max_cut = _clamp(4.9 - energy * 1.3, 2.3, 5.6)

    # Color stays conservative:
    contrast = _clamp(
        color.get("contrast_bias", 1.0),
        SAFE_GLOBAL_LIMITS["contrast"][0],
        SAFE_GLOBAL_LIMITS["contrast"][1],
    )
    saturation = _clamp(
        color.get("saturation_bias", 1.0),
        SAFE_GLOBAL_LIMITS["saturation"][0],
        SAFE_GLOBAL_LIMITS["saturation"][1],
    )

    # Music and SFX:
    music_volume = _clamp(
        0.09 + energy * 0.12,
        SAFE_GLOBAL_LIMITS["music_volume"][0],
        SAFE_GLOBAL_LIMITS["music_volume"][1],
    )
    sfx_volume = _clamp(
        0.04 + energy * 0.10,
        SAFE_GLOBAL_LIMITS["sfx_volume"][0],
        SAFE_GLOBAL_LIMITS["sfx_volume"][1],
    )

    return {
        "cut_duration": {
            "min": round(min_cut, 3),
            "max": round(max_cut, 3),
        },
        "motion": {
            "intensity": round(motion_intensity, 3),
            "family": profile.get("motion_family", "documentary_drift"),
        },
        "color": {
            "contrast": round(contrast, 3),
            "saturation": round(saturation, 3),
            "temperature": round(color.get("temperature", 0.0), 4),
            "tint": round(color.get("tint", 0.0), 4),
            "primary_color": color.get("primary"),
            "secondary_color": color.get("secondary"),
            "highlight_protection": 0.14,
            "shadow_lift": 0.025,
            "sharpness": 0.08,
            "bloom": 0.035,
            "light_leak": 0.018,
        },
        "audio": {
            "music_volume": round(music_volume, 3),
            "sfx_volume": round(sfx_volume, 3),
            "target_lufs": -14.0,
            "ducking_strength": round(_clamp(0.20 + energy * 0.18, 0.18, 0.36), 3),
        },
        "voice": {
            "profile": profile.get("voice_family", "warm_measured"),
            "humanization_strength": round(_clamp(0.45 + energy * 0.25, 0.42, 0.72), 3),
        },
        "captions": {
            "family": profile.get("caption_family", "documentary_clean"),
        },
        "transitions": {
            "family": profile.get("transition_family", "smooth_documentary"),
            "duration": round(_clamp(0.13 + energy * 0.12, 0.10, 0.30), 3),
        },
    }


# ==========================================================
# PRESET COMPATIBILITY HELPERS
# ==========================================================

def resolve_niche_key(niche_name):
    """
    Returns a stable key for config/history filenames.
    """
    clean = _clean_text(niche_name)
    if not clean:
        return "auto_general"

    clean = clean.replace(" ", "_").replace("-", "_")
    clean = re.sub(r"[^a-z0-9_]", "", clean)
    clean = re.sub(r"_+", "_", clean).strip("_")

    return clean or "auto_general"


def get_fixed_niches():
    return sorted(FIXED_NICHES)


def get_style_families():
    return deepcopy(STYLE_FAMILIES)


def get_color_families():
    return deepcopy(COLOR_FAMILIES)


# ==========================================================
# DEBUG
# ==========================================================

if __name__ == "__main__":
    samples = [
        ("luxury watches", "This is how wealthy people choose rare watches.", "short"),
        ("AI future robots", "Scientists revealed a new machine that changes everything.", "short"),
        ("dark mystery case", "The truth was hidden for decades.", "long"),
        ("modern bedroom design", "This small room transformation changed the whole space.", "short"),
    ]

    for niche, script, mode in samples:
        print("\n---")
        print(niche)
        result = analyze_niche(niche, script, mode)
        print("Primary:", result["primary_family"])
        print("Secondary:", result["secondary_family"])
        print("Confidence:", result["confidence"])
        print("Recommendations:", result["recommendations"])