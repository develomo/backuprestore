# editing_variation_engine.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# EDITING VARIATION ENGINE v1.0
# ==========================================================
# Purpose:
# - Same niche ke videos mein exact same editing repeat na ho.
# - Per-niche render history maintain kare.
# - 10+ safe variation recipes rotate kare.
# - Recipe repeat nonlinear/shuffled order mein ho.
# - Har render mein tiny professional variation apply kare.
# - Values safe range ke andar rahen taake clips kharab na hon.
#
# This is one of the most important anti-robotic systems.
# ==========================================================

import json
import random
import hashlib
from pathlib import Path
from copy import deepcopy
from datetime import datetime

from niche_intelligence_engine import resolve_niche_key


BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
VARIATION_DIR = CONFIG_DIR / "variation_history"
VARIATION_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# SAFE VARIATION RECIPE BANK
# ==========================================================
# These are not extreme filters.
# They are tiny human-editor-like adjustments.
# ==========================================================

VARIATION_RECIPES = [
    {
        "id": "recipe_01_clean_open",
        "label": "Clean Open",
        "motion_multiplier": 1.00,
        "cut_multiplier": 1.00,
        "contrast_delta": 0.000,
        "saturation_delta": 0.000,
        "brightness_delta": 0.000,
        "sharpness_delta": 0.000,
        "music_delta": 0.000,
        "sfx_delta": 0.000,
        "voice_pitch_delta": 0.000,
        "voice_pace_delta": 0.000,
        "transition_delta": 0.000,
        "caption_timing_offset": 0.000,
    },
    {
        "id": "recipe_02_soft_premium",
        "label": "Soft Premium",
        "motion_multiplier": 0.94,
        "cut_multiplier": 1.06,
        "contrast_delta": -0.008,
        "saturation_delta": -0.006,
        "brightness_delta": 0.004,
        "sharpness_delta": -0.010,
        "music_delta": -0.010,
        "sfx_delta": -0.012,
        "voice_pitch_delta": -0.006,
        "voice_pace_delta": -0.008,
        "transition_delta": 0.018,
        "caption_timing_offset": -0.015,
    },
    {
        "id": "recipe_03_crisp_editor",
        "label": "Crisp Editor",
        "motion_multiplier": 1.06,
        "cut_multiplier": 0.96,
        "contrast_delta": 0.010,
        "saturation_delta": 0.004,
        "brightness_delta": -0.003,
        "sharpness_delta": 0.012,
        "music_delta": 0.006,
        "sfx_delta": 0.006,
        "voice_pitch_delta": 0.004,
        "voice_pace_delta": 0.006,
        "transition_delta": -0.014,
        "caption_timing_offset": -0.020,
    },
    {
        "id": "recipe_04_cinematic_slow",
        "label": "Cinematic Slow",
        "motion_multiplier": 0.90,
        "cut_multiplier": 1.12,
        "contrast_delta": 0.006,
        "saturation_delta": -0.004,
        "brightness_delta": -0.002,
        "sharpness_delta": -0.004,
        "music_delta": 0.004,
        "sfx_delta": -0.008,
        "voice_pitch_delta": -0.004,
        "voice_pace_delta": -0.010,
        "transition_delta": 0.026,
        "caption_timing_offset": 0.000,
    },
    {
        "id": "recipe_05_retention_push",
        "label": "Retention Push",
        "motion_multiplier": 1.12,
        "cut_multiplier": 0.90,
        "contrast_delta": 0.006,
        "saturation_delta": 0.006,
        "brightness_delta": 0.000,
        "sharpness_delta": 0.006,
        "music_delta": 0.012,
        "sfx_delta": 0.014,
        "voice_pitch_delta": 0.006,
        "voice_pace_delta": 0.010,
        "transition_delta": -0.020,
        "caption_timing_offset": -0.025,
    },
    {
        "id": "recipe_06_documentary_flow",
        "label": "Documentary Flow",
        "motion_multiplier": 0.98,
        "cut_multiplier": 1.04,
        "contrast_delta": 0.002,
        "saturation_delta": -0.008,
        "brightness_delta": 0.002,
        "sharpness_delta": -0.002,
        "music_delta": -0.006,
        "sfx_delta": -0.014,
        "voice_pitch_delta": -0.002,
        "voice_pace_delta": -0.004,
        "transition_delta": 0.012,
        "caption_timing_offset": -0.010,
    },
    {
        "id": "recipe_07_modern_snap",
        "label": "Modern Snap",
        "motion_multiplier": 1.08,
        "cut_multiplier": 0.94,
        "contrast_delta": 0.008,
        "saturation_delta": 0.002,
        "brightness_delta": -0.004,
        "sharpness_delta": 0.010,
        "music_delta": 0.008,
        "sfx_delta": 0.010,
        "voice_pitch_delta": 0.003,
        "voice_pace_delta": 0.008,
        "transition_delta": -0.016,
        "caption_timing_offset": -0.018,
    },
    {
        "id": "recipe_08_emotional_space",
        "label": "Emotional Space",
        "motion_multiplier": 0.92,
        "cut_multiplier": 1.10,
        "contrast_delta": -0.004,
        "saturation_delta": -0.010,
        "brightness_delta": 0.004,
        "sharpness_delta": -0.006,
        "music_delta": -0.004,
        "sfx_delta": -0.016,
        "voice_pitch_delta": -0.005,
        "voice_pace_delta": -0.012,
        "transition_delta": 0.024,
        "caption_timing_offset": 0.000,
    },
    {
        "id": "recipe_09_premium_energy",
        "label": "Premium Energy",
        "motion_multiplier": 1.05,
        "cut_multiplier": 0.98,
        "contrast_delta": 0.004,
        "saturation_delta": 0.010,
        "brightness_delta": 0.000,
        "sharpness_delta": 0.004,
        "music_delta": 0.014,
        "sfx_delta": 0.006,
        "voice_pitch_delta": 0.004,
        "voice_pace_delta": 0.004,
        "transition_delta": -0.006,
        "caption_timing_offset": -0.018,
    },
    {
        "id": "recipe_10_minimal_human",
        "label": "Minimal Human",
        "motion_multiplier": 0.96,
        "cut_multiplier": 1.02,
        "contrast_delta": -0.002,
        "saturation_delta": -0.002,
        "brightness_delta": 0.002,
        "sharpness_delta": -0.004,
        "music_delta": -0.008,
        "sfx_delta": -0.006,
        "voice_pitch_delta": -0.003,
        "voice_pace_delta": -0.003,
        "transition_delta": 0.008,
        "caption_timing_offset": -0.012,
    },
    {
        "id": "recipe_11_high_clarity",
        "label": "High Clarity",
        "motion_multiplier": 1.03,
        "cut_multiplier": 0.99,
        "contrast_delta": 0.008,
        "saturation_delta": -0.002,
        "brightness_delta": 0.000,
        "sharpness_delta": 0.014,
        "music_delta": -0.002,
        "sfx_delta": 0.002,
        "voice_pitch_delta": 0.002,
        "voice_pace_delta": 0.002,
        "transition_delta": -0.004,
        "caption_timing_offset": -0.020,
    },
    {
        "id": "recipe_12_smooth_lux",
        "label": "Smooth Lux",
        "motion_multiplier": 0.95,
        "cut_multiplier": 1.08,
        "contrast_delta": 0.004,
        "saturation_delta": 0.004,
        "brightness_delta": 0.002,
        "sharpness_delta": -0.006,
        "music_delta": 0.006,
        "sfx_delta": -0.010,
        "voice_pitch_delta": -0.002,
        "voice_pace_delta": -0.006,
        "transition_delta": 0.018,
        "caption_timing_offset": -0.010,
    },
]


# Nonlinear repeat order after all recipes are used.
# This avoids: 1,2,3,4... repeat feeling.
RECIPE_REPEAT_SHUFFLE = [1, 6, 3, 9, 2, 11, 4, 8, 0, 10, 5, 7]


# ==========================================================
# SAFE LIMITS
# ==========================================================

DEFAULT_SAFE_LIMITS = {
    "contrast": (0.94, 1.07),
    "saturation": (0.92, 1.09),
    "brightness_shift": (-0.030, 0.030),
    "sharpness": (0.00, 0.18),
    "music_volume": (0.05, 0.24),
    "sfx_volume": (0.02, 0.18),
    "transition_seconds": (0.08, 0.36),
    "motion_intensity": (0.55, 1.75),
    "voice_pitch_delta": (-0.035, 0.035),
    "voice_pace_delta": (-0.045, 0.045),
    "caption_timing_offset": (-0.060, 0.030),
}


# ==========================================================
# HELPERS
# ==========================================================

def _clamp(value, low, high):
    return max(low, min(high, value))


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _history_path(niche_key):
    niche_key = resolve_niche_key(niche_key)
    return VARIATION_DIR / f"{niche_key}_variation_history.json"


def _load_history(niche_key):
    path = _history_path(niche_key)

    if not path.exists():
        return {
            "niche_key": resolve_niche_key(niche_key),
            "render_count": 0,
            "used_recipe_ids": [],
            "recent_recipe_ids": [],
            "last_updated": None,
            "renders": [],
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Invalid history format")
        data.setdefault("render_count", 0)
        data.setdefault("used_recipe_ids", [])
        data.setdefault("recent_recipe_ids", [])
        data.setdefault("renders", [])
        return data
    except Exception:
        return {
            "niche_key": resolve_niche_key(niche_key),
            "render_count": 0,
            "used_recipe_ids": [],
            "recent_recipe_ids": [],
            "last_updated": None,
            "renders": [],
        }


def _save_history(niche_key, history):
    path = _history_path(niche_key)
    history["last_updated"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def _stable_seed(*parts):
    raw = "|".join(str(p) for p in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _get_recipe_by_id(recipe_id):
    for recipe in VARIATION_RECIPES:
        if recipe["id"] == recipe_id:
            return deepcopy(recipe)
    return deepcopy(VARIATION_RECIPES[0])


def _choose_recipe(niche_key, history):
    """
    Chooses recipe in a non-repetitive way.
    First cycle:
        use recipes not already used.
    After full cycle:
        use nonlinear shuffled order.
    Also avoids last 3 recipes when possible.
    """
    render_count = int(history.get("render_count", 0))
    used_ids = set(history.get("used_recipe_ids", []))
    recent_ids = set(history.get("recent_recipe_ids", [])[-3:])

    all_ids = [r["id"] for r in VARIATION_RECIPES]

    available = [rid for rid in all_ids if rid not in used_ids and rid not in recent_ids]

    if not available:
        available = [rid for rid in all_ids if rid not in recent_ids]

    if not available:
        available = all_ids

    # Before all recipes used, deterministic random from available.
    if len(used_ids) < len(all_ids):
        seed = _stable_seed(niche_key, render_count, "first_cycle")
        rng = random.Random(seed)
        recipe_id = rng.choice(available)
        return _get_recipe_by_id(recipe_id)

    # After full cycle, nonlinear shuffle order.
    idx = RECIPE_REPEAT_SHUFFLE[render_count % len(RECIPE_REPEAT_SHUFFLE)]
    recipe_id = all_ids[idx]

    if recipe_id in recent_ids:
        fallback = [rid for rid in all_ids if rid not in recent_ids]
        seed = _stable_seed(niche_key, render_count, "fallback_cycle")
        rng = random.Random(seed)
        recipe_id = rng.choice(fallback or all_ids)

    return _get_recipe_by_id(recipe_id)


def _micro_jitter(niche_key, render_count, field, amount):
    """
    Tiny deterministic jitter.
    Same render gets stable values.
    Different render gets slightly different values.
    """
    seed = _stable_seed(niche_key, render_count, field)
    rng = random.Random(seed)
    return rng.uniform(-amount, amount)


def _apply_delta(value, delta, limits):
    value = _safe_float(value)
    low, high = limits
    return _clamp(value + delta, low, high)


def _apply_multiplier(value, multiplier, limits):
    value = _safe_float(value)
    low, high = limits
    return _clamp(value * multiplier, low, high)


# ==========================================================
# MAIN PUBLIC API
# ==========================================================

def build_variation_plan(niche_name, mode="short", editing_dna=None):
    """
    Creates one render-specific variation plan.

    Args:
        niche_name: selected niche/custom niche.
        mode: short/long.
        editing_dna: optional output from niche_intelligence_engine.

    Returns:
        dict variation plan.
    """
    niche_key = resolve_niche_key(niche_name)
    history = _load_history(niche_key)
    render_count = int(history.get("render_count", 0))

    recipe = _choose_recipe(niche_key, history)

    # Tiny extra randomness inside safe ranges.
    jitter = {
        "contrast": _micro_jitter(niche_key, render_count, "contrast", 0.006),
        "saturation": _micro_jitter(niche_key, render_count, "saturation", 0.006),
        "brightness": _micro_jitter(niche_key, render_count, "brightness", 0.006),
        "sharpness": _micro_jitter(niche_key, render_count, "sharpness", 0.008),
        "music": _micro_jitter(niche_key, render_count, "music", 0.010),
        "sfx": _micro_jitter(niche_key, render_count, "sfx", 0.008),
        "transition": _micro_jitter(niche_key, render_count, "transition", 0.012),
        "motion": _micro_jitter(niche_key, render_count, "motion", 0.035),
        "voice_pitch": _micro_jitter(niche_key, render_count, "voice_pitch", 0.006),
        "voice_pace": _micro_jitter(niche_key, render_count, "voice_pace", 0.008),
    }

    plan = {
        "niche_key": niche_key,
        "niche_name": str(niche_name or niche_key),
        "mode": str(mode or "short").lower(),
        "render_count": render_count,
        "recipe": recipe,
        "jitter": jitter,
        "safe_limits": deepcopy(DEFAULT_SAFE_LIMITS),
        "variation_strength": 0.0,
    }

    # Strength is useful for logs/UI.
    variation_strength = (
        abs(recipe.get("motion_multiplier", 1.0) - 1.0) * 1.5
        + abs(recipe.get("cut_multiplier", 1.0) - 1.0)
        + abs(recipe.get("contrast_delta", 0.0)) * 10
        + abs(recipe.get("saturation_delta", 0.0)) * 8
        + abs(recipe.get("voice_pace_delta", 0.0)) * 8
    )
    plan["variation_strength"] = round(_clamp(variation_strength, 0.0, 1.0), 3)

    return plan


def apply_variation_to_recommendations(recommendations, variation_plan):
    """
    Applies recipe/jitter to niche intelligence recommendations.

    Input:
        recommendations from niche_intelligence_engine.

    Output:
        adjusted settings still inside safe limits.
    """
    rec = deepcopy(recommendations or {})
    plan = variation_plan or {}
    recipe = plan.get("recipe", {})
    jitter = plan.get("jitter", {})
    limits = plan.get("safe_limits", DEFAULT_SAFE_LIMITS)

    # Ensure structures exist.
    rec.setdefault("color", {})
    rec.setdefault("motion", {})
    rec.setdefault("audio", {})
    rec.setdefault("voice", {})
    rec.setdefault("transitions", {})
    rec.setdefault("cut_duration", {})
    rec.setdefault("captions", {})

    # Color:
    rec["color"]["contrast"] = round(
        _apply_delta(
            rec["color"].get("contrast", 1.0),
            recipe.get("contrast_delta", 0.0) + jitter.get("contrast", 0.0),
            limits["contrast"],
        ),
        4,
    )

    rec["color"]["saturation"] = round(
        _apply_delta(
            rec["color"].get("saturation", 1.0),
            recipe.get("saturation_delta", 0.0) + jitter.get("saturation", 0.0),
            limits["saturation"],
        ),
        4,
    )

    rec["color"]["brightness_shift"] = round(
        _apply_delta(
            rec["color"].get("brightness_shift", 0.0),
            recipe.get("brightness_delta", 0.0) + jitter.get("brightness", 0.0),
            limits["brightness_shift"],
        ),
        4,
    )

    rec["color"]["sharpness"] = round(
        _apply_delta(
            rec["color"].get("sharpness", 0.08),
            recipe.get("sharpness_delta", 0.0) + jitter.get("sharpness", 0.0),
            limits["sharpness"],
        ),
        4,
    )

    # Motion:
    rec["motion"]["intensity"] = round(
        _apply_multiplier(
            rec["motion"].get("intensity", 1.0),
            recipe.get("motion_multiplier", 1.0) + jitter.get("motion", 0.0),
            limits["motion_intensity"],
        ),
        4,
    )

    # Cut duration:
    cut_min = _safe_float(rec["cut_duration"].get("min", 2.0), 2.0)
    cut_max = _safe_float(rec["cut_duration"].get("max", 4.0), 4.0)
    cut_mul = recipe.get("cut_multiplier", 1.0)

    rec["cut_duration"]["min"] = round(_clamp(cut_min * cut_mul, 1.0, 8.0), 3)
    rec["cut_duration"]["max"] = round(_clamp(cut_max * cut_mul, rec["cut_duration"]["min"] + 0.3, 10.0), 3)

    # Audio:
    rec["audio"]["music_volume"] = round(
        _apply_delta(
            rec["audio"].get("music_volume", 0.12),
            recipe.get("music_delta", 0.0) + jitter.get("music", 0.0),
            limits["music_volume"],
        ),
        4,
    )

    rec["audio"]["sfx_volume"] = round(
        _apply_delta(
            rec["audio"].get("sfx_volume", 0.08),
            recipe.get("sfx_delta", 0.0) + jitter.get("sfx", 0.0),
            limits["sfx_volume"],
        ),
        4,
    )

    # Voice:
    rec["voice"]["pitch_delta"] = round(
        _clamp(
            recipe.get("voice_pitch_delta", 0.0) + jitter.get("voice_pitch", 0.0),
            limits["voice_pitch_delta"][0],
            limits["voice_pitch_delta"][1],
        ),
        4,
    )
    rec["voice"]["pace_delta"] = round(
        _clamp(
            recipe.get("voice_pace_delta", 0.0) + jitter.get("voice_pace", 0.0),
            limits["voice_pace_delta"][0],
            limits["voice_pace_delta"][1],
        ),
        4,
    )

    # Transitions:
    rec["transitions"]["duration"] = round(
        _apply_delta(
            rec["transitions"].get("duration", 0.18),
            recipe.get("transition_delta", 0.0) + jitter.get("transition", 0.0),
            limits["transition_seconds"],
        ),
        4,
    )

    # Captions:
    rec["captions"]["timing_offset"] = round(
        _clamp(
            recipe.get("caption_timing_offset", 0.0),
            limits["caption_timing_offset"][0],
            limits["caption_timing_offset"][1],
        ),
        4,
    )

    rec["variation_recipe_id"] = recipe.get("id", "unknown")
    rec["variation_recipe_label"] = recipe.get("label", "Unknown")
    rec["render_count"] = plan.get("render_count", 0)
    rec["niche_key"] = plan.get("niche_key", "auto_general")

    return rec


def commit_variation_render(niche_name, variation_plan, output_path=None, status="success"):
    """
    Call this after successful render.
    Updates per-niche history.
    """
    niche_key = resolve_niche_key(niche_name)
    history = _load_history(niche_key)

    recipe = (variation_plan or {}).get("recipe", {})
    recipe_id = recipe.get("id", "unknown")

    history["render_count"] = int(history.get("render_count", 0)) + 1

    used = history.get("used_recipe_ids", [])
    if recipe_id not in used and recipe_id != "unknown":
        used.append(recipe_id)

    if len(used) >= len(VARIATION_RECIPES):
        # Keep used list but allow cycle logic to repeat after full bank.
        used = [r["id"] for r in VARIATION_RECIPES]

    recent = history.get("recent_recipe_ids", [])
    if recipe_id != "unknown":
        recent.append(recipe_id)
    recent = recent[-10:]

    render_record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "recipe_id": recipe_id,
        "recipe_label": recipe.get("label", "Unknown"),
        "output_path": str(output_path or ""),
        "status": status,
    }

    renders = history.get("renders", [])
    renders.append(render_record)
    renders = renders[-50:]

    history["used_recipe_ids"] = used
    history["recent_recipe_ids"] = recent
    history["renders"] = renders

    _save_history(niche_key, history)
    return deepcopy(history)


def get_variation_history(niche_name):
    return deepcopy(_load_history(resolve_niche_key(niche_name)))


def reset_variation_history(niche_name):
    path = _history_path(resolve_niche_key(niche_name))
    if path.exists():
        path.unlink()
    return True


# ==========================================================
# DEBUG
# ==========================================================

if __name__ == "__main__":
    niche = "luxury_lifestyle"

    for i in range(3):
        plan = build_variation_plan(niche, mode="short")
        print("\nRender:", i)
        print("Recipe:", plan["recipe"]["id"], plan["recipe"]["label"])
        print("Jitter:", plan["jitter"])
        commit_variation_render(niche, plan, output_path=f"test_{i}.mp4")