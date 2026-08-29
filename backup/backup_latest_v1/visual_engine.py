# visual_engine.py
# ==========================================================
# MY CREATION VIDEO GENERATOR
# PROFESSIONAL VISUAL ORCHESTRATOR v2.0
# ==========================================================
# Purpose:
# - Old apply_visual_pacing(video, mode="short") compatibility maintain karna.
# - Video clip par safe visual polish apply karna.
# - Color grading, effects, beat accents ko one place se call karna.
# - Over-editing avoid karna.
# - AI Editing Brain render_plan support karna.
#
# Important:
# Ye file heavy effects khud implement nahi karti.
# Ye orchestrator hai:
#   - color_grading.py
#   - effects_engine.py
#   - beat_sync_engine.py
#
# Professional rule:
# Agar pipeline already color/effects apply kar chuki hai,
# to is file ko skip bhi kiya ja sakta hai.
# ==========================================================

try:
    from color_grading import apply_safe_color_correction
except Exception:
    apply_safe_color_correction = None

try:
    from effects_engine import apply_visual_effects
except Exception:
    apply_visual_effects = None

try:
    from beat_sync_engine import apply_beat_flashes
except Exception:
    apply_beat_flashes = None


# ==========================================================
# HELPERS
# ==========================================================

def safe_print(message):
    try:
        print(str(message).replace("→", "->").replace("—", "-"), flush=True)
    except Exception:
        pass


def _mode_key(mode):
    mode = str(mode or "short").lower()
    if mode in ("long", "youtube_long", "horizontal"):
        return "long"
    return "short"


def _feature_enabled(render_plan, key, default=True):
    try:
        return bool(render_plan.get("feature_switches", {}).get(key, default))
    except Exception:
        return default


# ==========================================================
# PUBLIC API
# ==========================================================

def apply_visual_pacing(
    video,
    mode="short",
    niche=None,
    render_plan=None,
    words=None,
    apply_color=True,
    apply_effects=True,
    apply_accents=False,
):
    """
    Old-compatible function.

    Old behavior:
        return video

    New behavior:
        optionally applies safe visual polish.
    """
    if video is None:
        return video

    mode = _mode_key(mode)
    out = video

    # Color correction: original-safe, not heavy LUT.
    if apply_color and _feature_enabled(render_plan, "enable_color_safety", True):
        if apply_safe_color_correction is not None:
            try:
                out = apply_safe_color_correction(
                    out,
                    render_plan=render_plan,
                    niche=niche,
                )
            except Exception as e:
                safe_print(f"[VisualEngine] Color skipped: {e}")

    # Visual finishing effects: subtle bloom/grain/vignette.
    if apply_effects and _feature_enabled(render_plan, "enable_effects", True):
        if apply_visual_effects is not None:
            try:
                out = apply_visual_effects(
                    out,
                    niche=niche,
                    render_plan=render_plan,
                )
            except Exception as e:
                safe_print(f"[VisualEngine] Effects skipped: {e}")

    # Attention accents are optional because effects_engine may already add them.
    if apply_accents:
        if apply_beat_flashes is not None:
            try:
                keyword_times = []
                for w in words or []:
                    if isinstance(w, dict):
                        try:
                            keyword_times.append(float(w.get("start", 0)))
                        except Exception:
                            pass

                out = apply_beat_flashes(
                    out,
                    duration=getattr(out, "duration", None),
                    niche=niche,
                    mode=mode,
                    render_plan=render_plan,
                    keyword_times=keyword_times[:12],
                )
            except Exception as e:
                safe_print(f"[VisualEngine] Accents skipped: {e}")

    return out


def apply_visual_stack(video, mode="short", niche=None, render_plan=None, words=None):
    """
    Modern alias for pipeline.
    """
    return apply_visual_pacing(
        video=video,
        mode=mode,
        niche=niche,
        render_plan=render_plan,
        words=words,
        apply_color=True,
        apply_effects=True,
        apply_accents=False,
    )


def apply_clean_documentary_style(video, mode="short", niche=None, render_plan=None):
    """
    Minimal style helper.
    """
    return apply_visual_pacing(
        video=video,
        mode=mode,
        niche=niche,
        render_plan=render_plan,
        apply_color=True,
        apply_effects=False,
        apply_accents=False,
    )


if __name__ == "__main__":
    print("Professional Visual Orchestrator ready.")
