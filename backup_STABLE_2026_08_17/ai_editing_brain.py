# ai_editing_brain.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# AI EDITING BRAIN v1.0
# ==========================================================
# Purpose:
# - One central intelligence layer for Shorts and Long videos.
# - Combines:
#     1. Niche Intelligence
#     2. Script Understanding
#     3. Per-niche Variation History
#     4. Safe Professional Editing Ranges
#     5. CPU-friendly production settings
# - Returns one complete render plan used by both pipelines.
#
# Important:
# This engine does NOT apply video effects directly.
# It only decides what should happen.
# master_pipeline.py and safe_long_video_polished.py will use
# this render plan to actually edit videos.
# ==========================================================

import json
from pathlib import Path
from copy import deepcopy
from datetime import datetime

from niche_intelligence_engine import (
    analyze_niche,
    resolve_niche_key,
)

from editing_variation_engine import (
    build_variation_plan,
    apply_variation_to_recommendations,
    commit_variation_render,
    get_variation_history,
)

from caption_style_registry import (
    WORD_FOCUS,
    STORY_FLOW,
    resolve_caption_style,
    get_default_caption_style_id,
)


BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

BRAIN_LOG_DIR = CONFIG_DIR / "brain_logs"
BRAIN_LOG_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# PROJECT HARDWARE PROFILE
# ==========================================================
# User machine:
# - Intel i5-6300HQ
# - 8GB RAM
# - Intel HD 530
# - SSD
#
# So render plan must be CPU-safe:
# - Edit at lower resolution
# - Export/upscale at final stage
# - Avoid heavy per-frame operations when not needed
# - Keep effects minimal and professional
# ==========================================================

HARDWARE_PROFILE = {
    "cpu": "Intel Core i5-6300HQ",
    "ram_gb": 8,
    "gpu": "Intel HD Graphics 530",
    "cpu_only": True,
    "recommended_threads": 1,
    "max_memory_mode": "safe",
    "edit_resolution": "720p",
    "final_resolution": "1080p",
    "enable_4k": False,
}


# ==========================================================
# OUTPUT PROFILES
# ==========================================================

OUTPUT_PROFILES = {
    "short": {
        "mode": "short",
        "edit_size": (480, 854),
        "final_size": (480, 854),
        "fps": 24,
        "aspect": "9:16",
        "codec": "libx264",
        "audio_codec": "aac",
        "preset_fast": "veryfast",
        "preset_quality": "fast",
        "adaptive_bitrate": True,
        "min_bitrate": "18000k",
        "target_bitrate": "30000k",
        "max_bitrate": "45000k",
        "crf_quality": 18,
        "target_lufs": -14.0,
        "intro_allowed": False,
        "outro_allowed": False,
        "subscribe_overlay_allowed": False,
    },
    "long": {
        "mode": "long",
        "edit_size": (854, 480),
        "final_size": (854, 480),
        "fps": 24,
        "aspect": "16:9",
        "codec": "libx264",
        "audio_codec": "aac",
        "preset_fast": "veryfast",
        "preset_quality": "fast",
        "adaptive_bitrate": True,
        "min_bitrate": "16000k",
        "target_bitrate": "35000k",
        "max_bitrate": "65000k",
        "crf_quality": 19,
        "target_lufs": -14.0,
        "intro_allowed": True,
        "outro_allowed": True,
        "subscribe_overlay_allowed": True,
    },
}


# ==========================================================
# DEFAULT FEATURE SWITCHES
# ==========================================================

FEATURE_SWITCHES = {
    "enable_voice_humanization": True,
    "enable_silence_cleanup": True,
    "enable_music_ducking": True,
    "enable_sfx": True,
    "enable_captions": True,
    "enable_caption_previews": False,
    "enable_hook_overlay": True,
    "enable_end_cta": True,
    "enable_motion": True,
    "enable_keyword_zoom": True,
    "enable_smart_zoom": True,
    "enable_transitions": True,
    "enable_color_safety": True,
    "enable_effects": True,
    "enable_quality_audit": False,
    "enable_temp_asset_cleanup": True,
}


# ==========================================================
# CAPTION DEFAULTS
# ==========================================================

CAPTION_DEFAULTS = {
    "category": WORD_FOCUS,
    "style_id": get_default_caption_style_id(WORD_FOCUS),
    "story_style_id": get_default_caption_style_id(STORY_FLOW),
    "timing_correction_seconds": -0.025,
    "max_caption_delay_seconds": 0.060,
    "safe_margin_ratio": 0.08,
}


# ==========================================================
# UTILS
# ==========================================================

def _safe_mode(mode):
    mode = str(mode or "short").strip().lower()
    if mode in ("long", "youtube_long", "horizontal"):
        return "long"
    return "short"


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))


def _deep_merge(base, updates):
    result = deepcopy(base)
    for key, value in (updates or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _safe_json_dump(data, path):
    try:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"[AIEditingBrain] Could not write log: {e}", flush=True)


def _estimate_scene_complexity(niche_profile, script_text=None, asset_count=0):
    """
    Estimate complexity for adaptive bitrate/render decisions.

    AI-generated clips often have:
    - gradients
    - fine details
    - synthetic textures
    - fast camera movements

    So we keep bitrate reasonably high but not insane for CPU.
    """
    energy = _safe_float(
        niche_profile.get("editing_dna", {}).get("energy"),
        0.55
    )

    script_len = len(str(script_text or "").split())
    script_factor = _clamp(script_len / 180.0, 0.0, 1.0)
    asset_factor = _clamp(float(asset_count or 0) / 20.0, 0.0, 1.0)

    complexity = 0.40
    complexity += energy * 0.32
    complexity += script_factor * 0.15
    complexity += asset_factor * 0.13

    return round(_clamp(complexity, 0.35, 0.92), 3)


def _select_adaptive_bitrate(output_profile, complexity):
    """
    Returns bitrate settings based on scene complexity.

    Keeps values CPU-safe but high enough for 4K.
    """
    complexity = _clamp(_safe_float(complexity, 0.55), 0.0, 1.0)

    if complexity < 0.45:
        return {
            "bitrate": output_profile["min_bitrate"],
            "maxrate": output_profile["target_bitrate"],
            "bufsize": "60000k",
            "crf": output_profile["crf_quality"],
        }

    if complexity < 0.70:
        return {
            "bitrate": output_profile["target_bitrate"],
            "maxrate": output_profile["max_bitrate"],
            "bufsize": "80000k",
            "crf": output_profile["crf_quality"],
        }

    return {
        "bitrate": output_profile["max_bitrate"],
        "maxrate": output_profile["max_bitrate"],
        "bufsize": "100000k",
        "crf": max(16, output_profile["crf_quality"] - 1),
    }


def _resolve_caption_plan(
    caption_category=None,
    caption_style_id=None,
    render_count=0,
):
    """
    Resolves caption category/style safely.

    Supports:
    - Word Focus one-word captions.
    - Story Flow 3-4 words captions.
    """
    category = str(caption_category or CAPTION_DEFAULTS["category"]).strip()

    if category not in (WORD_FOCUS, STORY_FLOW):
        category = WORD_FOCUS

    fallback_id = get_default_caption_style_id(category)

    style = resolve_caption_style(
        style_id=caption_style_id or fallback_id,
        category=category,
        render_count=render_count,
    )

    if style.get("category") != category:
        style = resolve_caption_style(
            style_id=None,
            category=category,
            render_count=render_count,
        )

    if category == WORD_FOCUS:
        words_per_group = 1
        mode_label = "Word Focus"
    else:
        words_per_group = 4
        mode_label = "Story Flow"

    return {
        "category": category,
        "mode_label": mode_label,
        "style_id": style["id"],
        "style": style,
        "words_per_group": words_per_group,
        "timing_correction_seconds": CAPTION_DEFAULTS["timing_correction_seconds"],
        "max_caption_delay_seconds": CAPTION_DEFAULTS["max_caption_delay_seconds"],
        "safe_margin_ratio": CAPTION_DEFAULTS["safe_margin_ratio"],
    }


def _build_cpu_safe_render_settings(mode, complexity):
    output = deepcopy(OUTPUT_PROFILES[mode])
    bitrate = _select_adaptive_bitrate(output, complexity)

    settings = {
        "edit_width": output["edit_size"][0],
        "edit_height": output["edit_size"][1],
        "final_width": output["final_size"][0],
        "final_height": output["final_size"][1],
        "fps": output["fps"],
        "threads": HARDWARE_PROFILE["recommended_threads"],
        "codec": output["codec"],
        "audio_codec": output["audio_codec"],
        "preset": output["preset_fast"],
        "quality_preset": output["preset_quality"],
        "adaptive_bitrate": output["adaptive_bitrate"],
        "bitrate": bitrate["bitrate"],
        "maxrate": bitrate["maxrate"],
        "bufsize": bitrate["bufsize"],
        "crf": bitrate["crf"],
        "target_lufs": output["target_lufs"],
        "aspect": output["aspect"],
    }

    return settings


# ==========================================================
# MAIN BRAIN PLAN
# ==========================================================

def build_render_plan(
    mode="short",
    niche_name="auto",
    script_text=None,
    caption_category=None,
    caption_style_id=None,
    asset_count=0,
    user_overrides=None,
):
    """
    Builds one complete render plan for the pipeline.

    Args:
        mode: "short" or "long"
        niche_name: fixed niche or custom niche.
        script_text: optional script/transcript.
        caption_category: word_focus/story_flow.
        caption_style_id: selected caption preset.
        asset_count: number of source clips.
        user_overrides: optional dict for advanced UI settings.

    Returns:
        dict render plan.
    """
    mode = _safe_mode(mode)
    niche_key = resolve_niche_key(niche_name)

    niche_profile = analyze_niche(
        niche_name=niche_name,
        script_text=script_text,
        mode=mode,
    )

    variation_plan = build_variation_plan(
        niche_name=niche_name,
        mode=mode,
        editing_dna=niche_profile.get("editing_dna"),
    )

    recommendations = niche_profile.get("recommendations", {})
    adjusted_recommendations = apply_variation_to_recommendations(
        recommendations,
        variation_plan,
    )

    render_count = int(variation_plan.get("render_count", 0))

    caption_plan = _resolve_caption_plan(
        caption_category=caption_category,
        caption_style_id=caption_style_id,
        render_count=render_count,
    )

    complexity = _estimate_scene_complexity(
        niche_profile=niche_profile,
        script_text=script_text,
        asset_count=asset_count,
    )

    render_settings = _build_cpu_safe_render_settings(
        mode=mode,
        complexity=complexity,
    )

    output_profile = deepcopy(OUTPUT_PROFILES[mode])

    plan = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project": "My Creation Video Generator",
        "mode": mode,
        "niche_name": str(niche_name or "auto"),
        "niche_key": niche_key,
        "script_available": bool(str(script_text or "").strip()),
        "niche_profile": niche_profile,
        "variation_plan": variation_plan,
        "editing_settings": adjusted_recommendations,
        "caption_plan": caption_plan,
        "scene_complexity": complexity,
        "render_settings": render_settings,
        "output_profile": output_profile,
        "feature_switches": deepcopy(FEATURE_SWITCHES),
        "hardware_profile": deepcopy(HARDWARE_PROFILE),
        "notes": [
            "Effects are intentionally minimal and professional.",
            "Original AI clip quality should be preserved.",
            "Per-niche variation prevents robotic repeated editing.",
            "Adaptive bitrate is selected using estimated scene complexity.",
        ],
    }

    if user_overrides:
        plan = _deep_merge(plan, user_overrides)

    _write_brain_log(plan)

    print(
        "[AIEditingBrain] Plan created | "
        f"mode={mode} | niche={niche_key} | "
        f"family={niche_profile.get('primary_family')} | "
        f"recipe={variation_plan.get('recipe', {}).get('label')} | "
        f"caption={caption_plan.get('style_id')} | "
        f"complexity={complexity}",
        flush=True,
    )

    return plan


def _write_brain_log(plan):
    """
    Saves last and timestamped render plan.
    Helpful for debugging and audit.
    """
    try:
        niche_key = plan.get("niche_key", "auto_general")
        mode = plan.get("mode", "short")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        last_path = BRAIN_LOG_DIR / f"last_{mode}_{niche_key}.json"
        run_path = BRAIN_LOG_DIR / f"{timestamp}_{mode}_{niche_key}.json"

        _safe_json_dump(plan, last_path)
        _safe_json_dump(plan, run_path)
    except Exception as e:
        print(f"[AIEditingBrain] Log failed: {e}", flush=True)


def commit_render_success(render_plan, output_path=None):
    """
    Call this at the end of successful render.
    Commits variation history.
    """
    niche_name = render_plan.get("niche_name", "auto")
    variation_plan = render_plan.get("variation_plan", {})

    history = commit_variation_render(
        niche_name=niche_name,
        variation_plan=variation_plan,
        output_path=output_path,
        status="success",
    )

    print(
        "[AIEditingBrain] Render committed | "
        f"niche={resolve_niche_key(niche_name)} | "
        f"new_count={history.get('render_count')}",
        flush=True,
    )

    return history


def get_last_render_plan(mode="short", niche_name="auto"):
    """
    Reads the latest saved brain plan for debugging/UI.
    """
    mode = _safe_mode(mode)
    niche_key = resolve_niche_key(niche_name)
    path = BRAIN_LOG_DIR / f"last_{mode}_{niche_key}.json"

    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def preview_plan_summary(render_plan):
    """
    Returns compact summary for UI/logging.
    """
    if not render_plan:
        return {}

    edit = render_plan.get("editing_settings", {})
    caption = render_plan.get("caption_plan", {})
    niche_profile = render_plan.get("niche_profile", {})
    variation = render_plan.get("variation_plan", {})
    render_settings = render_plan.get("render_settings", {})

    return {
        "project": render_plan.get("project"),
        "mode": render_plan.get("mode"),
        "niche": render_plan.get("niche_name"),
        "primary_family": niche_profile.get("primary_family"),
        "secondary_family": niche_profile.get("secondary_family"),
        "confidence": niche_profile.get("confidence"),
        "recipe": variation.get("recipe", {}).get("label"),
        "caption_mode": caption.get("mode_label"),
        "caption_style": caption.get("style_id"),
        "fps": render_settings.get("fps"),
        "final_size": (
            render_settings.get("final_width"),
            render_settings.get("final_height"),
        ),
        "bitrate": render_settings.get("bitrate"),
        "motion_intensity": edit.get("motion", {}).get("intensity"),
        "color_contrast": edit.get("color", {}).get("contrast"),
        "color_saturation": edit.get("color", {}).get("saturation"),
        "music_volume": edit.get("audio", {}).get("music_volume"),
        "sfx_volume": edit.get("audio", {}).get("sfx_volume"),
        "voice_profile": edit.get("voice", {}).get("profile"),
    }


def get_niche_history_summary(niche_name):
    """
    UI/debug helper.
    """
    history = get_variation_history(niche_name)
    return {
        "niche_key": resolve_niche_key(niche_name),
        "render_count": history.get("render_count", 0),
        "recent_recipe_ids": history.get("recent_recipe_ids", []),
        "last_updated": history.get("last_updated"),
    }


# ==========================================================
# DEBUG
# ==========================================================

if __name__ == "__main__":
    plan = build_render_plan(
        mode="short",
        niche_name="luxury_lifestyle",
        script_text="This is what wealth looks like when discipline meets opportunity.",
        caption_category=WORD_FOCUS,
        caption_style_id=None,
        asset_count=12,
    )

    print(json.dumps(preview_plan_summary(plan), indent=2))