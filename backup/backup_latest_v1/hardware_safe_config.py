# hardware_safe_config.py
# ==========================================================
# Intel i5 6th gen + 8GB RAM profile
#
# UPDATED 2026-07-02:
#   All original constants below are UNCHANGED so ram_safe_render.py
#   (and any other file importing from here) keeps working exactly
#   as before. A new section has been ADDED at the bottom for the
#   fixed batch_long_renderer.py engine -- it controls the per-clip
#   "edit" render quality (fast/low-RAM) separately from the final
#   "delivery" quality (the one-time upscale pass at the end).
# ==========================================================
from pathlib import Path

# --- Edit + Final both 480p (no enhance, no upscale) ---
# NOTE: these ENABLE_UPSCALE / ENABLE_4K_FINAL flags are the LEGACY
# MoviePy-pipeline flags (used by ram_safe_render.py). They stay False
# here on purpose -- upscaling is now handled separately and more
# efficiently by batch_long_renderer.py's ffmpeg_final_upscale(), see
# BATCH_* settings below.
LOW_RAM_RENDER = True
SEQUENTIAL_EFFECT_RENDER = True
ENABLE_UPSCALE = False
ENABLE_4K_FINAL = False

# Short 9:16 @ 480w | Long 16:9 @ 480h
EDIT_SHORT_SIZE = (480, 854)
EDIT_LONG_SIZE = (854, 480)
FINAL_SHORT_SIZE = EDIT_SHORT_SIZE
FINAL_LONG_SIZE = EDIT_LONG_SIZE

EDIT_FPS = 24
RENDER_THREADS = 1
MAX_CAPTION_WORD_CLIPS = 200
MAX_CAPTION_PHRASE_CLIPS = 280
WHISPER_MODEL = "tiny"

FFMPEG_PRESET = "ultrafast"
FFMPEG_CRF = 23

RAM_TEMP_DIR_NAME = "_ram_safe_temp_render"

# ALL editing features ON — applied one step at a time at 480p
SAFE_FEATURES = {
    "enable_motion": True,
    "enable_animation": True,
    "enable_zoom": True,
    "enable_keyword_zoom": True,
    "enable_beat_sync": True,
    "enable_story_flow": True,
    "enable_hook_overlay": True,
    "enable_overlays": True,
    "enable_transitions": True,
    "enable_effects": True,
    "enable_captions": True,
    "enable_4k_final": False,
    "enable_upscale": False,
}

THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def apply_thread_limits():
    import os
    for key, val in THREAD_ENV.items():
        os.environ[key] = val


def ram_temp_dir(base_dir=None):
    base = Path(base_dir) if base_dir else Path(__file__).parent
    return base / RAM_TEMP_DIR_NAME


def clamp_fps(fps):
    try:
        return min(int(fps or EDIT_FPS), EDIT_FPS)
    except Exception:
        return EDIT_FPS


def caption_clip_limit(mode="word_by_word"):
    m = str(mode or "").lower()
    if m in ("phrase", "story_flow", "3_to_4"):
        return MAX_CAPTION_PHRASE_CLIPS
    return MAX_CAPTION_WORD_CLIPS


def force_safe_render_kwargs(kwargs):
    """Keep all editing ON — only block 4K/upscale and cap FPS."""
    if kwargs is None:
        kwargs = {}
    kwargs["fps"] = clamp_fps(kwargs.get("fps"))
    kwargs["final_4k"] = False
    kwargs["quality"] = "balanced"
    overrides = dict(kwargs.get("preset_overrides") or {})
    overrides.update({
        "final_4k": False,
        "fps": kwargs["fps"],
        "quality": "balanced",
    })
    kwargs["preset_overrides"] = overrides
    return kwargs


# ============================================================
# NEW: batch_long_renderer.py settings
# ============================================================
# BATCH_EDIT_QUALITY:
#   Resolution used while cutting/grading each of the 150 individual
#   clip segments. Keep this LOW (360p/480p) -- this is the RAM- and
#   time-sensitive stage since it runs once per clip, sequentially,
#   one ffmpeg process at a time (this is why your 8GB RAM machine
#   never actually runs out of memory in this engine -- MoviePy is
#   not used here at all, everything is direct ffmpeg subprocess
#   calls with only ONE clip in memory/disk-buffer at a time).
BATCH_EDIT_QUALITY = "480p"

# BATCH_FINAL_QUALITY:
#   Resolution of the file you actually upload to YouTube. This is a
#   SINGLE one-time ffmpeg upscale pass applied to the fully finished,
#   fully edited video (after all 150 clips + intro/outro/subscribe +
#   music/sfx have already been combined). Because it only runs once
#   (not per-clip), a 480p -> 1080p lanczos+sharpen pass on a ~19 min
#   video is realistic on an i5 6th gen without blowing past 8GB RAM.
#   Set to "480p" or "none" to skip the upscale entirely (fastest,
#   useful while you're testing/iterating on pacing and cuts).
BATCH_FINAL_QUALITY = "1080p"

# How many clips get rendered + concatenated per "batch" before that
# batch is written to disk and its temp segments deleted. Smaller =
# less peak disk/RAM per batch, slightly more ffmpeg process overhead.
BATCH_SIZE_DEFAULT = 8

# Encoder settings for the ONE-TIME final upscale pass only (not used
# for the 150 per-clip segments, which always use FFMPEG_PRESET/CRF
# above for maximum speed).
BATCH_UPSCALE_PRESET = "fast"
BATCH_UPSCALE_CRF = 20
BATCH_UPSCALE_ENABLE = True


def batch_render_settings():
    """Convenience accessor so batch_long_renderer.py (or app.py) can
    pull all batch-related settings in one call instead of importing
    each constant individually."""
    return {
        "edit_quality": BATCH_EDIT_QUALITY,
        "final_quality": BATCH_FINAL_QUALITY,
        "batch_size": BATCH_SIZE_DEFAULT,
        "upscale_preset": BATCH_UPSCALE_PRESET,
        "upscale_crf": BATCH_UPSCALE_CRF,
        "upscale_enable": BATCH_UPSCALE_ENABLE,
        "edit_preset": FFMPEG_PRESET,
        "edit_crf": FFMPEG_CRF,
    }